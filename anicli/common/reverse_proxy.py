"""
Primitive module for reverse-proxying playlists or videos to bypass CORS issues.
Rewrites playlist URLs to local URLs for reverse-proxy streaming.
Supports header proxying for seek operations (Range requests).

This module provides functionality for:
- HLS (HTTP Live Streaming) playlist proxying
- DASH (Dynamic Adaptive Streaming over HTTP) manifest proxying
- Binary content (video files) proxying with range request support
- URL rewriting for streaming content
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Literal, Optional, overload
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
    """
    Generator for static data (playlists).

    Args:
        data: Input data as bytes or string
        chunk_size: Size of chunks to yield, defaults to DEFAULT_CHUNK_SIZE

    Yields:
        Bytes in specified chunk sizes
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    with io.BytesIO(data) as bio:
        while chunk := bio.read(chunk_size):
            yield chunk


def _process_hls_line(line: str, url_target: str, url_rewriter: UrlRewriter, uri_pattern: re.Pattern) -> str:
    """
    Process a single HLS playlist line.

    Args:
        line: The HLS playlist line to process
        url_target: Target URL to join relative URLs with
        url_rewriter: Function to rewrite URLs
        uri_pattern: Regex pattern to match URI attributes

    Returns:
        Processed line with rewritten URLs where applicable
    """
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
    """
    Process HLS playlist (.m3u8).

    Args:
        url_target: Target URL of the HLS playlist
        client: HTTPX async client for making requests
        url_rewriter: Function to rewrite URLs in the playlist
        headers: Optional headers to send with the request
        chunk_size: Size of chunks for yielding data

    Returns:
        ProxyResponse containing the processed HLS playlist content
    """
    resp = await client.get(url_target, headers=headers)
    resp.raise_for_status()

    uri_pattern = re.compile(r'(URI=")([^"]+)(")')
    processed_lines = [
        _process_hls_line(line.strip(), url_target, url_rewriter, uri_pattern) for line in resp.text.splitlines()
    ]

    playlist_content = "\n".join(processed_lines).encode("utf-8")

    # Form response headers
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
    """
    Process DASH MPD XML.

    Args:
        root: Root XML element of the DASH manifest
        url_target: Target URL to join relative URLs with
        url_rewriter: Function to rewrite URLs in the XML
    """
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
    """
    Process DASH MPD manifest (.mpd).

    Args:
        url_target: Target URL of the DASH manifest
        client: HTTPX async client for making requests
        url_rewriter: Function to rewrite URLs in the manifest
        headers: Optional headers to send with the request
        chunk_size: Size of chunks for yielding data

    Returns:
        ProxyResponse containing the processed DASH manifest content
    """
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
    Proxy binary content (mp4, ts) with Range request support.
    Uses client.send(stream=True) instead of context manager to access headers.

    Args:
        url_target: Target URL of the binary content
        client: HTTPX async client for making requests
        headers: Optional headers to send with the request
        chunk_size: Size of chunks for yielding data

    Returns:
        ProxyResponse containing the binary content stream
    """
    request = client.build_request("GET", url_target, headers=headers)

    # Send the request but don't read the body immediately (stream=True)
    resp = await client.send(request, stream=True)

    # IMPORTANT: In case of error (404, 500) we should close the connection immediately,
    # if we don't intend to read the body (or read and discard the error)
    if resp.is_error:
        await resp.aclose()
        resp.raise_for_status()

    # Headers that are critical for video player
    forward_headers = ["content-type", "content-length", "content-range", "accept-ranges", "last-modified", "etag"]

    response_headers = {}
    for key in forward_headers:
        if val := resp.headers.get(key):
            response_headers[key] = val

    # Add CORS
    response_headers["Access-Control-Allow-Origin"] = "*"

    # Create a wrapper generator that will close the httpx connection after streaming completes
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
    mode: Literal["hls", "dash", "binary", "auto"],
    headers: Headers | dict[str, str] | None = ...,
    chunk_size: int = ...,
) -> ProxyResponse: ...


@overload
async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: None = None,
    mode: Literal["hls", "dash", "binary", "auto"] = "binary",
    headers: Headers | dict[str, str] | None = ...,
    chunk_size: int = ...,
) -> ProxyResponse: ...


async def stream(
    url_target: str,
    client: AsyncClient,
    url_rewriter: UrlRewriter | None = None,
    mode: Literal["hls", "dash", "binary", "auto"] = "auto",
    headers: Headers | dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> ProxyResponse:
    """
    Universal function for proxying video streams and playlists.
    Returns ProxyResponse with generator and headers.

    Args:
        url_target: Target URL to proxy
        client: HTTPX async client for making requests
        url_rewriter: Function to rewrite URLs (required for HLS/DASH modes)
        mode: Processing mode ("auto", "hls", "dash", or "binary")
        headers: Optional headers to send with the request
        chunk_size: Size of chunks for yielding data

    Returns:
        ProxyResponse containing the processed content stream

    Raises:
        ValueError: If url_rewriter is not provided when required for HLS/DASH modes
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
