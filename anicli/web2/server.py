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


storage = MemoryStorage()
app = FastAPI(docs_url=None, redoc_url=None)
http_client: Optional[httpx.AsyncClient] = None


@app.on_event("startup")
async def startup_event():
    global http_client
    http_client = httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        follow_redirects=True,
        verify=False,
    )
    print(f"\n{'=' * 60}")
    print(f"Server started at: http://127.0.0.1:8000/?token={TOKEN}")
    print(f"{'=' * 60}\n")


@app.on_event("shutdown")
async def shutdown_event():
    if http_client:
        await http_client.aclose()


# --- HELPERS ---


def encode_state(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode()


def decode_state(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode()).decode()


def create_url_rewriter(base_proxy_url: str, h_b64: Optional[str] = None):
    def rewriter(original_url: str) -> str:
        params = []
        if "$" in original_url:
            params.append(f"url={quote(original_url, safe=':/$')}")
        else:
            params.append(f"url_b64={encode_state(original_url)}")
        if h_b64:
            params.append(f"h_b64={h_b64}")
        return f"{base_proxy_url}?{'&'.join(params)}"

    return rewriter


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
async def index(request: Request):
    extractors = get_extractor_modules()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "extractors": extractors,
            "current_extractor": "animego",
        },
    )


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str, source: str):
    extractor_cls = dynamic_load_extractor_module(source)
    if not extractor_cls:
        raise HTTPException(404, "Extractor not found")
    extractor = extractor_cls.Extractor()
    results = await extractor.a_search(q)
    data = [{"uid": storage.save(r), "title": r.title, "meta": r} for r in results]
    return templates.TemplateResponse("grid.html", {"request": request, "items": data, "title": f"Search: {q}"})


@app.get("/ongoing", response_class=HTMLResponse)
async def ongoing(request: Request, source: str = "animego"):
    extractor_cls = dynamic_load_extractor_module(source)
    if not extractor_cls:
        raise HTTPException(404, "Extractor not found")
    extractor = extractor_cls.Extractor()
    results = await extractor.a_ongoing()
    data = [{"uid": storage.save(r), "title": r.title, "meta": r} for r in results]
    return templates.TemplateResponse("grid.html", {"request": request, "items": data, "title": "Ongoings"})


@app.get("/anime/{uid}", response_class=HTMLResponse)
async def anime_details(request: Request, uid: str):
    result = storage.get(uid)
    if not result:
        raise HTTPException(404, "Object expired")

    anime = await result.a_get_anime()
    episodes = await anime.a_get_episodes()

    ep_data = []
    for ep in episodes:
        ep_uid = storage.save(ep)
        ep_data.append(
            {
                "uid": ep_uid,
                "title": ep.title,
                "num": str(ep.num) if hasattr(ep, "num") else str(getattr(ep, "ordinal", "?")),
            }
        )

    # Передаем anime_uid (текущий uid), чтобы потом вернуться к списку или навигироваться
    return templates.TemplateResponse(
        "episodes.html", {"request": request, "anime": anime, "episodes": ep_data, "anime_uid": uid}
    )


# --- UNIFIED PLAYER CONTROLLER ---


@app.get("/play/{episode_uid}", response_class=HTMLResponse)
async def player(request: Request, episode_uid: str, anime_uid: Optional[str] = None, source_index: int = 0):
    """
    Единый интерфейс плеера.
    episode_uid: ID текущего эпизода
    anime_uid: ID аниме (для навигации пред/след)
    source_index: Индекс выбранного источника озвучки (по умолчанию 0)
    """
    episode = storage.get(episode_uid)
    if not episode:
        raise HTTPException(404, "Episode not found")

    # 1. Получаем источники для текущего эпизода
    sources = await episode.a_get_sources()
    if not sources:
        return HTMLResponse("<h3>No sources found for this episode</h3>")

    # Валидация индекса источника
    if source_index < 0 or source_index >= len(sources):
        source_index = 0

    current_source = sources[source_index]

    # 2. Получаем видео для выбранного источника
    videos: List[Video] = await current_source.a_get_videos()

    # Подготовка Artplayer
    artplayer_quality = []
    base_proxy = str(request.url_for("proxy_stream"))
    videos.sort(key=lambda v: v.quality, reverse=True)

    for vid in videos:
        h_b64 = None
        if vid.headers:
            h_json = json.dumps(vid.headers)
            h_b64 = encode_state(h_json)

        rewriter = create_url_rewriter(base_proxy, h_b64)
        proxied_url = rewriter(vid.url)
        v_type = "m3u8" if vid.type == "hls" else vid.type

        artplayer_quality.append(
            {
                "default": vid.quality == 1080,
                "html": f"{vid.quality}p ({vid.type})",
                "url": proxied_url,
                "type": v_type,
            }
        )

    if not artplayer_quality:
        return HTMLResponse("<h3>No video streams found</h3>")

    default_url = artplayer_quality[0]["url"]
    default_type = artplayer_quality[0]["type"]

    # 3. Логика навигации (Next/Prev/Jump)
    nav_context = {}
    if anime_uid:
        anime_obj = storage.get(anime_uid)
        # Если объект аниме жив, пытаемся получить список эпизодов для навигации
        # Важно: мы не делаем сетевой запрос снова, если `anime` объект кэширует эпизоды,
        # иначе придется делать await anime.a_get_episodes().
        # В anicli-api обычно get_episodes делает запрос.
        # Чтобы не тормозить, можно попробовать достать из кэша extractor-а, но для надежности сделаем запрос.
        # Т.к. это локальный сервер для 1 юзера, доп. запрос приемлем.
        if anime_obj:
            # Получаем все эпизоды чтобы найти соседей
            # (Примечание: это может быть медленно на тяжелых сайтах, но необходимо для навигации)
            try:
                # В идеале здесь нужен кэш, но пока straightforward
                all_episodes = await anime_obj.a_get_episodes()

                # Ищем индекс текущего
                current_idx = -1
                for idx, ep in enumerate(all_episodes):
                    # Сравниваем по атрибутам, т.к. объекты могут быть пересозданы
                    if str(ep.num) == str(episode.num) and ep.title == episode.title:
                        current_idx = idx
                        break

                if current_idx != -1:
                    nav_context["current_num"] = str(episode.num)

                    # Prev
                    if current_idx > 0:
                        prev_ep = all_episodes[current_idx - 1]
                        nav_context["prev_uid"] = storage.save(prev_ep)

                    # Next
                    if current_idx < len(all_episodes) - 1:
                        next_ep = all_episodes[current_idx + 1]
                        nav_context["next_uid"] = storage.save(next_ep)

                    # Для Jump списка
                    nav_context["total_episodes"] = len(all_episodes)
                    # Можно передать мапу {номер: uid} для JS перехода, но это много данных.
                    # Сделаем проще: при вводе номера будем искать его (через отдельный легкий роут или перебор при submit)
            except Exception as e:
                print(f"Nav error: {e}")

    # Подготовка списка источников для UI
    sources_ui = []
    for idx, src in enumerate(sources):
        netloc = urlparse(src.url).netloc if hasattr(src, "url") and src.url else "Unknown"
        sources_ui.append(
            {
                "index": idx,
                "title": src.title,  # Озвучка/Плеер
                "netloc": netloc,
                "selected": idx == source_index,
            }
        )

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
        },
    )


@app.get("/play_jump", response_class=RedirectResponse)
async def player_jump(request: Request, anime_uid: str, ep_num: str):
    """Хелпер для перехода к конкретному номеру эпизода"""
    anime_obj = storage.get(anime_uid)
    if not anime_obj:
        raise HTTPException(404, "Anime context lost")

    episodes = await anime_obj.a_get_episodes()
    target_ep = next((e for e in episodes if str(e.num) == ep_num), None)

    if target_ep:
        uid = storage.save(target_ep)
        return RedirectResponse(url=f"/play/{uid}?anime_uid={anime_uid}")

    # Если не нашли, возвращаемся назад (можно добавить error msg)
    return RedirectResponse(url=request.headers.get("referer", "/"))


# --- PROXY STREAMING ---
@app.get("/proxy", name="proxy_stream")
async def proxy_stream(
    request: Request, url: Optional[str] = None, url_b64: Optional[str] = None, h_b64: Optional[str] = None
):
    target_url = url if url else decode_state(url_b64) if url_b64 else None
    if not target_url:
        raise HTTPException(400, "Missing url")

    headers = {}
    if h_b64:
        try:
            headers = json.loads(decode_state(h_b64))
        except:
            pass

    allow = ["range", "accept", "accept-encoding", "user-agent"]
    for k, v in request.headers.items():
        if k.lower() in allow:
            if k.lower() == "range":
                headers["Range"] = v
            elif k.lower() not in headers:
                headers[k] = v

    base_proxy_url = str(request.url_for("proxy_stream"))
    rewriter = create_url_rewriter(base_proxy_url, h_b64)

    try:
        stream_ctx = await stream(
            target_url, http_client, rewriter, mode="auto", request_headers=headers, chunk_size=64 * 1024
        )
        return StreamingResponse(
            stream_ctx, media_type="application/octet-stream", headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        print(f"Proxy Error: {e}")
        raise HTTPException(502, f"Upstream error: {e}")
