from collections.abc import Sequence

from anicli_api.player.base import Video

_M3U_HEADER = "#EXTM3U"
_M3U_ITEM = "#EXTINF:0,{name}\n{url}"
_M3U_SEP = "\n\n"


def generate_m3u_str_playlist(videos: Sequence[Video], titles: Sequence[str]) -> str:
    assert len(videos) == len(titles), "videos and titles sequences must have same length"
    playlist_items = [_M3U_HEADER]
    for video, title in zip(videos, titles):
        playlist_items.append(_M3U_ITEM.format(name=title, url=video.url))
    return _M3U_SEP.join(playlist_items)
