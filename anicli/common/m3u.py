from collections.abc import Sequence

from anicli_api.player.base import Video

_M3U_HEADER = "#EXTM3U"
_M3U_ITEM = "#EXTINF:0,{name}\n{url}"
_M3U_SEP = "\n\n"


def generate_m3u_str_playlist(videos: Sequence[Video], titles: Sequence[str]) -> str:
    if len(videos) != len(titles):
        raise ValueError(
            f"Length mismatch: {len(videos)} videos and {len(titles)} titles provided."
        )
    playlist_items = [_M3U_HEADER]
    playlist_items.extend(
        _M3U_ITEM.format(name=title, url=video.url)
        for video, title in zip(videos, titles)
    )
    return _M3U_SEP.join(playlist_items)
