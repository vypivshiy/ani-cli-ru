import tempfile
from contextlib import contextmanager
from typing import TYPE_CHECKING, List, Tuple
from urllib.parse import urlsplit

from anicli_api.tools.m3u import Playlist

if TYPE_CHECKING:
    from anicli.utils.cached_extractor import CachedItemAsyncContext
    from anicli_api.base import BaseSource, Video, BaseEpisode, BaseAnime

__all__ = [
    'new_tmp_playlist',
    'make_playlist_items'
]


@contextmanager
def new_tmp_playlist(playlist_raw: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u') as temp_file:
        temp_file.write(playlist_raw)
    try:
        yield temp_file.name
    finally:
        temp_file.close()


def source_hash(source: "BaseSource") -> int:
    return hash((source.title, urlsplit(source.url).netloc))


def create_player_title(episode: 'BaseEpisode', source: 'BaseSource', anime: 'BaseAnime') -> str:
    return f'{episode.num} {episode.title} ({source.title}) - {anime.title}'


async def make_playlist_items(context: 'CachedItemAsyncContext') -> Tuple[List['Video'], List[str]]:
    # TODO: convert to chunked iterator
    indexes = context.picked_episode_indexes
    base_video = context.picked_video
    base_source = context.picked_source

    episodes = [context.episodes[i] for i in indexes]

    # this hash value helps pick required videos
    base_source_hash = source_hash(base_source)

    video_urls: List['Video'] = []
    video_titles: List['str'] = []
    for episode in episodes:
        sources = await context.extractor.a_get_sources(episode)
        # pick source
        for source in sources:
            if base_source_hash == source_hash(source):
                break
        else:
            print('out')
            break

        videos = await context.extractor.a_get_videos(source)
        for video in videos:
            if video == base_video:
                video_urls.append(video)
                video_titles.append(
                    create_player_title(episode, source, context.anime)
                )
                break
    return video_urls, video_titles


def save_playlist_to_tmp(playlist_raw: str) -> str:
    """return path to temporary playlist file"""
