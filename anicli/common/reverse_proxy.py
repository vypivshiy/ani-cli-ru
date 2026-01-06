"""Примитивный модуль для reverse-proxy плейлистов или видео для обхода проблемы CORS.
Переписывает URL плейлистов на локальный URL, для reverse-proxy streaming

WARNING:
    Работает только в базовых случаях, не покрыты большинство corner-cases. Например, не работает с okcdn плейлистами и видео

СМ: использовании в реализации локального веб клиента на fastapi
"""
from __future__ import annotations

import io
import re
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Optional, overload
from urllib.parse import urljoin

if TYPE_CHECKING:
    from httpx import AsyncClient, Headers
    from lxml.etree import Element

from lxml import etree  # type: ignore

UrlRewriter = Callable[[str], str]

# Constants
ALLOWED_HEADERS = frozenset(
    {
        "range",
        "auth",
        "authorization",
        "cookie",
        "user-agent",
        "accept",
        "accept-encoding",
        "referer",
        "x-requested-with",
    }
)
DEFAULT_CHUNK_SIZE = 4096


async def _yield_bytes(data: bytes | str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> AsyncGenerator[bytes, None]:
    if isinstance(data, str):
        data = data.encode("utf-8")

    with io.BytesIO(data) as bio:
        while chunk := bio.read(chunk_size):
            yield chunk


def _process_hls_line(line: str, url_target: str, url_rewriter: UrlRewriter, uri_pattern: re.Pattern) -> str:
    """Обрабатывает одну строку HLS плейлиста."""
    if not line or line.startswith("#EXTINF") or line.startswith("#EXT-X-"):
        # Пропускаем пустые строки и метаданные без URI
        if "URI=" not in line:
            return line

    # Обработка сегментов (строки без #)
    if not line.startswith("#"):
        abs_url = urljoin(url_target, line)
        return url_rewriter(abs_url)

    # Обработка атрибутов с URI (ключи, субтитры)
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
    headers: Optional[Headers] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
):
    """Обрабатывает HLS плейлист (.m3u8). Переписывает все URL."""
    resp = await client.get(url_target, headers=headers)
    resp.raise_for_status()

    uri_pattern = re.compile(r'(URI=")([^"]+)(")')
    processed_lines = [
        _process_hls_line(line.strip(), url_target, url_rewriter, uri_pattern) for line in resp.text.splitlines()
    ]

    playlist_content = "\n".join(processed_lines)
    async for chunk in _yield_bytes(playlist_content, chunk_size):
        yield chunk


def _process_dash_xml(
    root: Element,  # type: ignore (lxml-stub install)
    url_target: str,
    url_rewriter: UrlRewriter,
) -> None:
    """Обрабатывает DASH MPD XML. Переписывает все URL."""
    ns = dict(root.nsmap)
    if None in ns:
        ns["d"] = ns.pop(None)

    def rewrite_attribute(node, attr_name: str) -> None:
        # Переписать атрибут узла, если он существует
        if val := node.get(attr_name):
            abs_url = urljoin(url_target, val)
            node.set(attr_name, url_rewriter(abs_url))

    def rewrite_text(node) -> None:
        # Переписать текстовое содержимое узла
        if node.text:
            text = node.text.strip()
            abs_url = urljoin(url_target, text)
            node.text = url_rewriter(abs_url)

    xpath_prefix = "d:" if "d" in ns else ""

    # BaseURL
    for node in root.xpath(f".//{xpath_prefix}BaseURL", namespaces=ns):
        rewrite_text(node)

    # SegmentTemplate (initialization, media)
    for node in root.xpath(f".//{xpath_prefix}SegmentTemplate", namespaces=ns):
        rewrite_attribute(node, "initialization")
        rewrite_attribute(node, "media")

    # SegmentURL (SegmentList)
    for node in root.xpath(f".//{xpath_prefix}SegmentURL", namespaces=ns):
        rewrite_attribute(node, "media")


async def reverse_stream_dash(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter,
    headers: Optional[Headers] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
):
    """Обрабатывает DASH MPD манифест (.mpd). Переписывает все URL."""
    resp = await client.get(url_target, headers=headers)
    resp.raise_for_status()

    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(resp.content, parser=parser)
        _process_dash_xml(root, url_target, url_rewriter)
        xml_bytes = etree.tostring(root, encoding="utf-8", xml_declaration=True)
    except Exception:
        # Fallback: отдать оригинальный контент при ошибке парсинга
        xml_bytes = resp.content

    async for chunk in _yield_bytes(xml_bytes, chunk_size):
        yield chunk


async def reverse_stream_binary(
    url_target: str,
    client: AsyncClient,
    headers: Optional[Headers] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
):
    """Проксировать бинарный контент (видео сегменты, медиа файлы)."""
    request_headers = {}

    # Range header extract request
    range_val = None
    if headers:
        range_val = next((v for k, v in headers.items() if k.lower() == "range"), None)
    if range_val:
        request_headers["Range"] = range_val

    async with client.stream("GET", url_target, headers=request_headers) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes(chunk_size):
            yield chunk


@overload
async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter,
    mode: str,  # "hls" | "dash"
    request_headers: Optional[Headers] = ...,
    chunk_size: int = ...,
) -> AsyncGenerator[bytes, None]: ...


@overload
async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: None = None,
    mode: str = "binary",
    request_headers: Optional[Headers] = ...,
    chunk_size: int = ...,
) -> AsyncGenerator[bytes, None]: ...


async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: Optional[UrlRewriter] = None,
    mode: str = "auto",
    request_headers: Optional[Headers] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
):
    """
    Универсальная функция для проксирования видео потоков и плейлистов.

    Args:
        url_target: URL для проксирования
        client: HTTP клиент
        url_rewriter: Функция для переписывания URL (обязательна для hls/dash)
        mode: Режим обработки ("auto", "hls", "dash", "binary")
        request_headers: Дополнительные заголовки запроса
        chunk_size: Размер чанка для стриминга

    Returns:
        Асинхронный генератор байтов
    """
    # Автоопределение типа контента по расширению
    if mode == "auto":
        clean_path = url_target.split("?")[0].lower()
        if clean_path.endswith(".m3u8"):
            mode = "hls"
        elif clean_path.endswith(".mpd"):
            mode = "dash"
        else:
            mode = "binary"

    # Маршрутизация на соответствующий обработчик
    if mode == "hls":
        if not url_rewriter:
            raise ValueError("url_rewriter is required when mode='hls' or mode='dash'")
        return reverse_stream_hls(url_target, client, url_rewriter, request_headers, chunk_size)
    elif mode == "dash":
        if not url_rewriter:
            raise ValueError("url_rewriter is required when mode='hls' or mode='dash'")
        return reverse_stream_dash(url_target, client, url_rewriter, request_headers, chunk_size)
    else:
        # dont need rewrire urls in playlist callback function
        return reverse_stream_binary(url_target, client, request_headers, chunk_size)
