from typing import Union, Optional, Mapping, List, Generator
import re

from anicli_api.player.base import Video
from httpx import Client


ATTR_LIST_PATTERN = re.compile(r"""((?:[^,"']|"[^"]*"|'[^']*')+)""")

__all__ = ["m3u8_stream_segments", "m3u8_parse_manifest", "mp4_stream"]


def m3u8_parse_manifest(video: Union["Video", str], headers: Optional[Mapping[str, str]] = None
                        ) -> List["Video"]:
    if isinstance(video, str) and video.endswith(".m3u8"):
        url = video
        headers = headers or {}
    elif isinstance(video, Video) and video.type == "m3u8":
        url = video
        headers = video.headers
    else:
        raise TypeError("Video should be `m3u8`")

    results: List["Video"] = []
    response = Client(headers=headers).get(url=url, follow_redirects=True)
    url_target = re.sub(r"\w+\.m3u8$", "", url)
    quality = 0

    for line in response.iter_lines():
        for word in ATTR_LIST_PATTERN.split(line):
            if match := re.search(r"(:?\d+)x(\d+)", word):
                quality = int(match[2])
            elif ".m3u8" in word:
                path = re.search(r"\w+\.m3u8", word)[0]  # type: ignore
                results.append(Video(type="m3u8", quality=quality, url=url_target + path, headers=headers))  # type: ignore
                quality = 0
    return results

def _stream_segment(url: str, headers: dict) -> Generator[str, None, None]:
    with Client().stream("GET", url, headers=headers, follow_redirects=True) as r:
        yield from r.iter_bytes()


def m3u8_stream_segments(video: Union["Video", str], headers: Optional[dict] = None):
    if isinstance(video, Video):
        url = video.url
        headers = video.headers
    else:
        url = video
        headers = headers
    response = Client(follow_redirects=True, headers=headers).get(url)
    url_target = re.sub(r"\w+\.m3u8$", "", url)
    for line in response.iter_lines():
        for word in ATTR_LIST_PATTERN.split(line):
            if ".m4s" in word or ".ts" in word:
                if match := re.search(r"\w+\.\w{2,3}", word):
                    segment_url = url_target + match[0]
                    yield from _stream_segment(segment_url, headers)


def mp4_stream(url: str, headers: dict):
    with Client(headers=headers, follow_redirects=True).stream("GET", url) as r:
        yield from r.iter_bytes()
