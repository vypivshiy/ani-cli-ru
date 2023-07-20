from typing import TYPE_CHECKING, List, Generator, Tuple
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from anicli_api.base import BaseSource, BaseEpisode
    from anicli_api.player.base import Video

__all__ = ["slice_play_hash", "slice_playlist_iter"]


def slice_play_hash(video: "Video", source: "BaseSource"):
    """generate hash key for slice video play"""
    return hash((urlsplit(video.url).netloc, video.type, video.quality, source.dub))


def slice_playlist_iter(episodes: List["BaseEpisode"], cmp_key_hash: int
                        ) -> Generator[Tuple["Video", "BaseEpisode"], None, None]:
    """Compare video by video url netloc, video type, quality and dubber name"""
    visited = set()
    for episode in episodes:
        if episode.num not in visited:
            for source in episode.get_sources():
                for video in source.get_videos():
                    if cmp_key_hash == slice_play_hash(video, source):
                        visited.add(episode.num)
                        yield video, episode
                        break
                if episode.num in visited:
                    break
