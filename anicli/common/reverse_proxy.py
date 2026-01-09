"""
Примитивный модуль для reverse-proxy плейлистов или видео для обхода проблемы CORS.
Переписывает URL плейлистов на локальный URL, для reverse-proxy streaming.
Поддерживает проксирование заголовков для seek (Range requests).
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Optional, overload
from urllib.parse import urljoin

if TYPE_CHECKING:
    from httpx import AsyncClient, Headers
    from lxml.etree import Element

from lxml import etree  # type: ignore

UrlRewriter = Callable[[str], str]
DEFAULT_CHUNK_SIZE = 4096


@dataclass
class ProxyResponse:
    content: AsyncGenerator[bytes, None]
    headers: dict[str, str]
    status_code: int


async def _yield_bytes(data: bytes | str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> AsyncGenerator[bytes, None]:
    """Генератор для статических данных (плейлистов)."""
    if isinstance(data, str):
        data = data.encode("utf-8")

    with io.BytesIO(data) as bio:
        while chunk := bio.read(chunk_size):
            yield chunk


def _process_hls_line(line: str, url_target: str, url_rewriter: UrlRewriter, uri_pattern: re.Pattern) -> str:
    """Обрабатывает одну строку HLS плейлиста."""
    if not line or line.startswith("#EXTINF") or line.startswith("#EXT-X-"):
        if "URI=" not in line:
            return line

    if not line.startswith("#"):
        abs_url = urljoin(url_target, line)
        return url_rewriter(abs_url)

    if "URI=" in line:

        def replace_uri(match):
            prefix, rel_url, suffix = match.groups()
            abs_url = urljoin(url_target, rel_url)
            return f"{prefix}{url_rewriter(abs_url)}{suffix}"

        return uri_pattern.sub(replace_uri, line)
    return line


async def reverse_stream_hls(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter,
    headers: Headers | dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ProxyResponse:
    """Обрабатывает HLS плейлист (.m3u8)."""
    resp = await client.get(url_target, headers=headers)
    resp.raise_for_status()

    uri_pattern = re.compile(r'(URI=")([^"]+)(")')
    processed_lines = [
        _process_hls_line(line.strip(), url_target, url_rewriter, uri_pattern) for line in resp.text.splitlines()
    ]

    playlist_content = "\n".join(processed_lines).encode("utf-8")

    # Формируем заголовки для ответа
    response_headers = {
        "Content-Type": resp.headers.get("Content-Type", "application/vnd.apple.mpegurl"),
        "Content-Length": str(len(playlist_content)),
        "Access-Control-Allow-Origin": "*",
    }

    return ProxyResponse(
        content=_yield_bytes(playlist_content, chunk_size),
        headers=response_headers,
        status_code=200,
    )


def _process_dash_xml(
    root: Element,
    url_target: str,
    url_rewriter: UrlRewriter,
) -> None:
    """Обрабатывает DASH MPD XML."""
    ns = dict(root.nsmap)
    if None in ns:
        ns["d"] = ns.pop(None)

    def rewrite_attribute(node, attr_name: str) -> None:
        if val := node.get(attr_name):
            abs_url = urljoin(url_target, val)
            node.set(attr_name, url_rewriter(abs_url))

    def rewrite_text(node) -> None:
        if node.text:
            text = node.text.strip()
            abs_url = urljoin(url_target, text)
            node.text = url_rewriter(abs_url)

    xpath_prefix = "d:" if "d" in ns else ""

    for node in root.xpath(f".//{xpath_prefix}BaseURL", namespaces=ns):
        rewrite_text(node)

    for node in root.xpath(f".//{xpath_prefix}SegmentTemplate", namespaces=ns):
        rewrite_attribute(node, "initialization")
        rewrite_attribute(node, "media")

    for node in root.xpath(f".//{xpath_prefix}SegmentURL", namespaces=ns):
        rewrite_attribute(node, "media")


async def reverse_stream_dash(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter,
    headers: Headers | dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ProxyResponse:
    """Обрабатывает DASH MPD манифест (.mpd)."""
    resp = await client.get(url_target, headers=headers)
    resp.raise_for_status()

    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(resp.content, parser=parser)
        _process_dash_xml(root, url_target, url_rewriter)
        xml_bytes = etree.tostring(root, encoding="utf-8", xml_declaration=True)
    except Exception:
        xml_bytes = resp.content

    response_headers = {
        "Content-Type": resp.headers.get("Content-Type", "application/dash+xml"),
        "Content-Length": str(len(xml_bytes)),
        "Access-Control-Allow-Origin": "*",
    }

    return ProxyResponse(
        content=_yield_bytes(xml_bytes, chunk_size),
        headers=response_headers,
        status_code=200,
    )


async def reverse_stream_binary(
    url_target: str,
    client: AsyncClient,
    headers: Headers | dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ProxyResponse:
    """
    Проксирует бинарный контент (mp4, ts) с поддержкой Range requests.
    Использует client.send(stream=True) вместо context manager для доступа к заголовкам.
    """
    request = client.build_request("GET", url_target, headers=headers)

    # Отправляем запрос, но не читаем тело сразу (stream=True)
    resp = await client.send(request, stream=True)

    # ВАЖНО: В случае ошибки (404, 500) мы должны сразу закрыть соединение,
    # если не собираемся читать тело (или прочитать и выбросить ошибку)
    if resp.is_error:
        await resp.aclose()
        resp.raise_for_status()

    # Заголовки, которые критичны для видео-плеера
    forward_headers = ["content-type", "content-length", "content-range", "accept-ranges", "last-modified", "etag"]

    response_headers = {}
    for key in forward_headers:
        if val := resp.headers.get(key):
            response_headers[key] = val

    # Добавляем CORS
    response_headers["Access-Control-Allow-Origin"] = "*"

    # Создаем генератор-обертку, который закроет соединение httpx после завершения стриминга
    async def stream_wrapper():
        try:
            async for chunk in resp.aiter_bytes(chunk_size):
                yield chunk
        finally:
            await resp.aclose()

    return ProxyResponse(content=stream_wrapper(), headers=response_headers, status_code=resp.status_code)


@overload
async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter,
    mode: str,
    headers: Headers | dict[str, str] | None = ...,
    chunk_size: int = ...,
) -> ProxyResponse: ...


@overload
async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: None = None,
    mode: str = "binary",
    headers: Headers | dict[str, str] | None = ...,
    chunk_size: int = ...,
) -> ProxyResponse: ...


async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter | None = None,
    mode: str = "auto",
    headers: Headers | dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ProxyResponse:
    """
    Универсальная функция для проксирования видео потоков и плейлистов.
    Возвращает ProxyResponse с генератором и заголовками.
    """
    if mode == "auto":
        clean_path = url_target.split("?")[0].lower()
        if clean_path.endswith(".m3u8"):
            mode = "hls"
        elif clean_path.endswith(".mpd"):
            mode = "dash"
        else:
            mode = "binary"

    if mode == "hls":
        if not url_rewriter:
            raise ValueError("url_rewriter is required when mode='hls'")
        return await reverse_stream_hls(url_target, client, url_rewriter, headers, chunk_size)

    elif mode == "dash":
        if not url_rewriter:
            raise ValueError("url_rewriter is required when mode='dash'")
        return await reverse_stream_dash(url_target, client, url_rewriter, headers, chunk_size)

    else:
        return await reverse_stream_binary(url_target, client, headers, chunk_size)
