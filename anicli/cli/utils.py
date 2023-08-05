
from typing import TYPE_CHECKING, List, Generator, Tuple, cast
from urllib.parse import urlsplit

from anicli.cli.config import AnicliApp

if TYPE_CHECKING:
    from anicli_api.base import BaseSource, BaseEpisode
    from anicli_api.player.base import Video
    from anicli.cli.config import Config

__all__ = ["slice_play_hash", "slice_playlist_iter", "sort_video_by_quality"]


def slice_play_hash(video: "Video", source: "BaseSource"):
    """generate hash key for slice video play"""
    return hash((urlsplit(video.url).netloc, video.type, video.quality, source.dub))


def slice_playlist_iter(episodes: List["BaseEpisode"], cmp_key_hash: int, config: "Config"
                        ) -> Generator[Tuple["Video", "BaseEpisode"], None, None]:
    """Compare video by video url netloc, video type, quality and dubber name"""
    # get main instance
    app = AnicliApp.__app_instances__["anicli-main"]
    app = cast(AnicliApp, app)

    visited = set()
    for episode in episodes:
        if episode.num not in visited:
            for source in episode.get_sources():
                for video in source.get_videos(**app.CFG.httpx_kwargs()):
                    if cmp_key_hash == slice_play_hash(video, source):
                        visited.add(episode.num)
                        yield video, episode
                        break
                if episode.num in visited:
                    break


def sort_video_by_quality(videos: List["Video"], quality: int) -> List["Video"]:
    if result := [video for video in videos if video.quality >= quality]:
        return result
    # not founded, get maximum value
    return [max(videos, key=lambda v: v.quality)]
