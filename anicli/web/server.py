import base64
import json
import secrets
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx
from anicli_api.player.base import Video
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from anicli.common.extractors import dynamic_load_extractor_module, get_extractor_modules
from anicli.common.reverse_proxy import stream

# --- CONFIGURATION ---
TOKEN = secrets.token_urlsafe(16)
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class Options:
    CHUNK_SIZE = 1024*1024  # 1M
    EXTRACTOR_NAME = "animego"
    MAX_QUALITY = 2060
    TTL = 3600 # seconds

OPTIONS = Options()


# --- MEMORY STORAGE ---
class MemoryStorage:
    def __init__(self):
        # Хранилище: UUID -> Object
        self.objects: Dict[str, Any] = {}
        # Кэш для быстрого поиска UUID по id(object) чтобы не дублировать
        self._cache_ids: Dict[int, str] = {}

    def save(self, obj: Any) -> str:
        """Сохраняет объект и возвращает UUID. Если объект уже есть, вернет старый UUID"""
        obj_id = id(obj)
        if obj_id in self._cache_ids:
            return self._cache_ids[obj_id]

        uid = str(uuid.uuid4())
        self.objects[uid] = obj
        self._cache_ids[obj_id] = uid
        return uid

    def get(self, uid: str) -> Any:
        return self.objects.get(uid)


class HeaderStorage:
    def __init__(self):
        self._store: dict[str, dict[str, str]] = {}

    def save(self, headers: dict[str, str]) -> str:
        hid = uuid.uuid4().hex
        self._store[hid] = headers
        return hid

    def get(self, hid: str) -> dict[str, str] | None:
        return self._store.get(hid)


header_storage = HeaderStorage()
storage = MemoryStorage()
app = FastAPI(docs_url=None, redoc_url=None)
http_client = httpx.AsyncClient(
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    follow_redirects=True,
    verify=False,
)


def generate_qr_code(url: str) -> str:
    """Генерирует QR код для URL в терминал используя ASCII (без зависимостей)"""
    try:
        # Легковесная библиотека только для терминала
        import segno
        qr = segno.make(url)
        
        # Рендерим в терминал как Unicode блоки
        from io import StringIO
        out = StringIO()
        qr.terminal(out=out, border=1, compact=True)
        return out.getvalue()
    except ImportError:
        # Fallback: простая текстовая ссылка
        return f"Install 'segno' for QR code: pip install segno\nOr scan this URL manually: {url}"


@app.on_event("startup")
async def startup_event():
    url = f"http://127.0.0.1:8000/?token={TOKEN}"
    print(f"\n{'=' * 60}")
    print(f"Server started at: {url}")
    print(f"{'=' * 60}")
    
    # Генерируем QR код
    print("\nScan QR code to access from mobile:")
    print(generate_qr_code(url))
    print(f"\n{'=' * 60}\n")


@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()


# --- HELPERS ---


def encode_state(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode()


def decode_state(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode()).decode()


def create_url_rewriter(base_proxy_url: str, hid: Optional[str] = None):
    def rewriter(original_url: str) -> str:
        if "$" in original_url:
            # DASH template — сохраняем $ как есть
            url_param = f"url={quote(original_url, safe=':/?$=&$')}"
        else:
            # Обычный URL — base64
            url_param = f"url_b64={encode_state(original_url)}"

        if hid:
            return f"{base_proxy_url}?{url_param}&hid={hid}"
        return f"{base_proxy_url}?{url_param}"

    return rewriter


def get_preferred_source(request: Request) -> str:
    """Получает предпочитаемый источник из cookie или параметра"""
    source = request.query_params.get("source")
    if not source:
        source = request.cookies.get("preferred_source", OPTIONS.EXTRACTOR_NAME)
    return source


def set_source_cookie(response: Response, source: str):
    """Устанавливает cookie с предпочитаемым источником"""
    response.set_cookie(key="preferred_source", value=source, max_age=30*24*60*60)  # 30 дней


# --- MIDDLEWARE & AUTH ---


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/favicon.ico"]:
        return await call_next(request)

    query_token = request.query_params.get("token")
    if query_token == TOKEN:
        response = await call_next(request)
        response.set_cookie(key="auth_token", value=TOKEN, httponly=True)
        return response

    cookie_token = request.cookies.get("auth_token")
    if cookie_token == TOKEN:
        return await call_next(request)

    if request.url.path == "/" and not query_token:
        return HTMLResponse("<h1>Unauthorized</h1><p>Check console for token link.</p>", status_code=403)
    return HTMLResponse("<h1>Unauthorized</h1>", status_code=403)


# --- ROUTES ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, response: Response, source: str = None):
    if source is None:
        source = get_preferred_source(request)
    
    extractors = get_extractor_modules()

    # Проверяем, что выбранный source существует
    if source not in extractors:
        source = OPTIONS.EXTRACTOR_NAME

    # Сохраняем выбранный источник
    set_source_cookie(response, source)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "extractors": extractors,
            "current_extractor": source,
        },
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, response: Response, q: str, source: str = None):
    if source is None:
        source = get_preferred_source(request)
    
    extractor_cls = dynamic_load_extractor_module(source)
    if not extractor_cls:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Extractor Not Found",
                "error_message": f"The extractor '{source}' was not found.",
                "back_url": "/"
            }
        )
    
    # Сохраняем выбранный источник
    set_source_cookie(response, source)
    
    extractor = extractor_cls.Extractor()
    results = await extractor.a_search(q)
    data = [{"uid": storage.save(r), "title": r.title, "meta": r} for r in results]
    
    extractors = get_extractor_modules()
    
    return templates.TemplateResponse(
        "grid.html",
        {
            "request": request,
            "items": data,
            "title": f"Search: {q}",
            "search_query": q,
            "extractors": extractors,
            "current_extractor": source,
            "back_url": "/"
        }
    )


@app.get("/ongoing", response_class=HTMLResponse)
async def ongoing(request: Request, response: Response, source: str = None):
    """Список онгоингов с поддержкой выбора extractor"""
    if source is None:
        source = get_preferred_source(request)
    
    extractor_cls = dynamic_load_extractor_module(source)
    if not extractor_cls:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Extractor Not Found",
                "error_message": f"The extractor '{source}' was not found.",
                "back_url": "/"
            }
        )
    
    # Сохраняем выбранный источник
    set_source_cookie(response, source)
    
    extractor = extractor_cls.Extractor()
    results = await extractor.a_ongoing()
    data = [{"uid": storage.save(r), "title": r.title, "meta": r} for r in results]

    # Получаем список всех extractors для навигации
    extractors = get_extractor_modules()

    return templates.TemplateResponse(
        "ongoing.html",
        {
            "request": request,
            "items": data,
            "title": "Ongoings",
            "extractors": extractors,
            "current_extractor": source,
            "back_url": "/"
        },
    )


@app.get("/anime/{uid}", response_class=HTMLResponse)
async def anime_details(request: Request, uid: str, from_page: str = None):
    result = storage.get(uid)
    if not result:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Anime Not Found",
                "error_message": "The anime you're looking for has expired or doesn't exist.",
                "back_url": from_page or "/"
            }
        )

    anime = await result.a_get_anime()
    episodes = await anime.a_get_episodes()

    # Сохраняем все эпизоды в storage и собираем данные
    ep_data = []
    all_episodes_info = []

    for ep in episodes:
        ep_uid = storage.save(ep)
        ep_num = str(ep.num) if hasattr(ep, "num") else str(getattr(ep, "ordinal", "?"))

        ep_data.append(
            {
                "uid": ep_uid,
                "title": ep.title,
                "num": ep_num,
            }
        )

        all_episodes_info.append({"uid": ep_uid, "num": ep_num, "title": ep.title})

    # Сохраняем список эпизодов для переиспользования в player
    episodes_list_uid = storage.save(all_episodes_info)
    
    # Определяем URL для возврата
    back_url = from_page if from_page else "/"

    return templates.TemplateResponse(
        "episodes.html",
        {
            "request": request,
            "anime": anime,
            "episodes": ep_data,
            "anime_uid": uid,
            "episodes_list_uid": episodes_list_uid,
            "back_url": back_url
        },
    )


# --- UNIFIED PLAYER CONTROLLER ---


@app.get("/play/{episode_uid}", response_class=HTMLResponse)
async def player(
    request: Request,
    episode_uid: str,
    anime_uid: Optional[str] = None,
    episodes_list_uid: Optional[str] = None,
    source_index: int = 0,
    from_page: str = None,
):
    episode = storage.get(episode_uid)
    if not episode:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Episode Not Found",
                "error_message": "The episode you're trying to watch has expired or doesn't exist.",
                "back_url": f"/anime/{anime_uid}" if anime_uid else "/"
            }
        )

    sources = await episode.a_get_sources()
    if not sources:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "No Sources Found",
                "error_message": "No video sources are available for this episode.",
                "back_url": f"/anime/{anime_uid}" if anime_uid else "/"
            }
        )

    if source_index < 0 or source_index >= len(sources):
        source_index = 0

    current_source = sources[source_index]
    # okcdn case:
    # для успешного трансляции видеопотока без обновления через API ok.ru
    # 
    # useragent запроса и видеопотока должны совпадать
    videos: List[Video] = await current_source.a_get_videos(headers={"User-Agent": request.headers.get("User-Agent", "Mozilla/5.0")})

    if not videos:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "No Video Streams",
                "error_message": "No video streams were found for this source.",
                "back_url": f"/anime/{anime_uid}" if anime_uid else "/"
            }
        )

    base_proxy = str(request.url_for("proxy_stream"))
    artplayer_quality = []

    videos.sort(key=lambda v: v.quality, reverse=True)

    for vid in videos:
        hid = None
        if vid.headers:
            # headers гарантированно корректны и специфичны для этого Video
            hid = header_storage.save(vid.headers)

        rewriter = create_url_rewriter(base_proxy, hid=hid)
        proxied_url = rewriter(vid.url)

        if vid.type == "hls":
            v_type = "m3u8"
        elif vid.type == "dash":
            v_type = "mpd"
        else:
            v_type = vid.type

        artplayer_quality.append(
            {
                "default": vid.quality == 1080,
                "html": f"{vid.quality}p ({vid.type})",
                "url": proxied_url,
                "type": v_type,
            }
        )

    default_url = artplayer_quality[0]["url"]
    default_type = artplayer_quality[0]["type"]

    # --- Навигация по эпизодам ---
    nav_context = {}
    all_episodes_data = []

    if episodes_list_uid:
        all_episodes_data = storage.get(episodes_list_uid) or []

        current_idx = next(
            (i for i, ep in enumerate(all_episodes_data) if ep["uid"] == episode_uid),
            -1,
        )

        if current_idx != -1:
            nav_context.update(
                {
                    "current_idx": current_idx,
                    "current_num": all_episodes_data[current_idx]["num"],
                    "total_episodes": len(all_episodes_data),
                }
            )

            if current_idx > 0:
                nav_context["prev_uid"] = all_episodes_data[current_idx - 1]["uid"]
                nav_context["prev_num"] = all_episodes_data[current_idx - 1]["num"]

            if current_idx < len(all_episodes_data) - 1:
                nav_context["next_uid"] = all_episodes_data[current_idx + 1]["uid"]
                nav_context["next_num"] = all_episodes_data[current_idx + 1]["num"]

    sources_ui = [
        {
            "index": idx,
            "title": src.title,
            "netloc": urlparse(src.url).netloc if src.url else "Unknown",
            "selected": idx == source_index,
        }
        for idx, src in enumerate(sources)
    ]
    
    # Определяем URL для возврата
    back_url = f"/anime/{anime_uid}" if anime_uid else (from_page if from_page else "/")

    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "quality_json": json.dumps(artplayer_quality),
            "default_url": default_url,
            "default_type": default_type,
            "title": f"Playing: {episode.title}",
            "sources": sources_ui,
            "current_source_index": source_index,
            "nav": nav_context,
            "episode_uid": episode_uid,
            "anime_uid": anime_uid,
            "episodes_list_uid": episodes_list_uid,
            "all_episodes": all_episodes_data,
            "all_episodes_json": json.dumps(all_episodes_data),
            "back_url": back_url,
            "from_page": from_page
        },
    )


# --- PROXY STREAMING ---
@app.get("/proxy", name="proxy_stream")
async def proxy_stream(
    request: Request,
    url: Optional[str] = None,
    url_b64: Optional[str] = None,
    hid: Optional[str] = None,
):
    target_url = url or (decode_state(url_b64) if url_b64 else None)
    if not target_url:
        raise HTTPException(400, "Missing url")

    upstream_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    if hid:
        # Получаем заголовки из хранилища (если есть)
        video_headers = header_storage.get(hid)
        if video_headers:
            upstream_headers.update(video_headers)

    # --- КЛЮЧЕВОЙ МОМЕНТ 1: Проброс Range ---
    # Браузер/плеер при перемотке отправляет Range: bytes=1234-
    if "range" in request.headers:
        upstream_headers["Range"] = request.headers["range"]

    base_proxy_url = str(request.url_for("proxy_stream"))
    rewriter = create_url_rewriter(base_proxy_url, hid=hid)

    try:
        # Получаем ProxyResponse (заголовки уже у нас, а стрим еще не начался)
        proxy_ctx = await stream(
            target_url,
            http_client,
            rewriter,
            headers=upstream_headers,
            mode="auto",
            chunk_size=OPTIONS.CHUNK_SIZE,  # Чуть больше чанк для бинарников
        )

        return StreamingResponse(
            proxy_ctx.content,
            status_code=proxy_ctx.status_code,
            headers=proxy_ctx.headers,
            media_type=proxy_ctx.headers.get("content-type", "application/octet-stream"),
        )

    except Exception as e:
        # Логирование
        print(f"Proxy error for {target_url}: {e}")
        raise HTTPException(502, f"Upstream error: {e}")
