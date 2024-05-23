from typing import TYPE_CHECKING, Generator, List, Tuple, cast
from urllib.parse import urlsplit

from anicli_api.player.aniboom import Aniboom
from httpx import Client

from anicli.cli.config import AnicliApp

if TYPE_CHECKING:
    from anicli_api.base import BaseEpisode, BaseSource
    from anicli_api.player.base import Video

    from anicli.cli.config import Config


def slice_play_hash(video: "Video", source: "BaseSource"):
    """generate hash key for slice video play"""
    video_netloc = urlsplit(video.url).netloc

    if source.url == Aniboom():
        # aniboom return random subdomains in Video objects
        # examples:
        # evie.yagami-light.com emily.yagami-light.com
        # amelia.yagami-light.com calcium.yagami-light.com
        video_netloc = ".".join(video_netloc.split(".")[-2:])
    return hash((video_netloc, video.type, video.quality, source.title))


def slice_playlist_iter(
    episodes: List["BaseEpisode"], cmp_key_hash: int, config: "Config"
) -> Generator[Tuple["BaseEpisode", "BaseSource", "Video"], None, None]:
    """Compare video by video url netloc, video type, quality and dubber name"""
    # get main instance
    app = AnicliApp.__app_instances__["anicli-main"]
    app = cast(AnicliApp, app)

    visited = set()
    for episode in episodes:
        if episode.num not in visited:
            for source in episode.get_sources():
                for video in source.get_videos(**config.httpx_kwargs()):
                    if cmp_key_hash == slice_play_hash(video, source):
                        visited.add(episode.num)
                        yield episode, source, video
                        break
                if episode.num in visited:
                    break


def sort_video_by_quality(videos: List["Video"], quality: int) -> List["Video"]:
    if result := [video for video in videos if video.quality >= quality]:
        return result
    # not founded, get maximum value
    return [max(videos, key=lambda v: v.quality)]


def get_preferred_quality_index(videos: List["Video"], quality: int) -> int:
    max_quality = 0
    i = 0
    for i, video in enumerate(videos):
        if video.quality >= quality:
            return i
        max_quality = max(video.quality, max_quality)
    return i


def get_preferred_human_quality_index(videos: List["Video"], quality: int) -> int:
    return get_preferred_quality_index(videos, quality) + 1


def is_video_url_valid(video: "Video") -> bool:
    # head method maybe don't work, but we can send GET request without read all content
    with Client().stream("GET", video.url, headers=video.headers) as r:
        # 200-299 OK, 302 - FOUND returns True, else False
        return r.is_success or r.status_code == 302  # noqa
