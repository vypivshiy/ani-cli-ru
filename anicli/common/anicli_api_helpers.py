from typing import AsyncGenerator, Callable, List, Tuple
from urllib.parse import urlsplit

from anicli_api.base import BaseAnime, BaseEpisode, BaseSource
from anicli_api.player.base import Video


def source_hash(source: "BaseSource") -> int:
    """default hash function helper for build playlist"""
    return hash((source.title, urlsplit(source.url).netloc))


def default_batch_gen_title(anime: BaseAnime, episode: BaseEpisode, _source: BaseSource, _video: Video) -> str:
    return f"{anime.title} - {episode.num} {episode.title}"


T_TITLE_GEN_CB = Callable[[BaseAnime, BaseEpisode, BaseSource, Video], str]


async def videos_iterator(
    episodes: List[BaseEpisode],
    *,
    initial_anime: BaseAnime,
    initial_source: BaseSource,
    initial_video: Video,
    cb_title: T_TITLE_GEN_CB = default_batch_gen_title,
) -> AsyncGenerator[Tuple[Video, str], None]:
    """video iterator helper functions for reuse in playlist-like features

    how it works:
    1. iterate in episodes
    2. iterate in source and compare dubber name (source.title) and base player url.netloc
    3. iterate until not found player provider (apologize, not exists target video with required dubber and player provider)

    Args:
        episodes: episodes to iterate over
        initial_anime: initial anime object (for title)
        initial_source: initial source (for compare in search)
        initial_video: initial video (for compare in search)
        cb_title: callback generator title for video

    Returns:
        async iterator with video and title objects
    """
    # predicate compare sources in iterator
    base_hash = source_hash(initial_source)

    for episode in episodes:
        sources = await episode.a_get_sources()
        for source in sources:
            if base_hash == source_hash(source):
                break
        else:
            # not founded by source hash - exit from generator
            break
        videos = await source.a_get_videos()
        for video in videos:
            if video.quality == initial_video.quality:
                yield video, cb_title(initial_anime, episode, source, video)
                break
