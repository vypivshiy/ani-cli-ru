import tempfile
from contextlib import contextmanager
from typing import TYPE_CHECKING, List, Tuple
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from anicli_api.base import Video, BaseSource, BaseAnime, BaseEpisode


# TODO: move to anicli-api package

def get_video_by_quality(requested_quality: int, videos: List['Video']) -> 'Video':
    """get video by quality
    if current quality not exist - get closest
    """
    if not videos:
        raise TypeError('No videos specified')

    closest_video = min(
        videos,
        key=lambda video: abs(video.quality - requested_quality)
    )

    return closest_video


def source_hash(source: "BaseSource") -> int:
    return hash((source.title, urlsplit(source.url).netloc))


def create_player_title(episode: 'BaseEpisode', source: 'BaseSource', anime: 'BaseAnime') -> str:
    return f'{episode.num} {episode.title} ({source.title}) - {anime.title}'


def iter_slice_videos(*,
                      anime: 'BaseAnime',
                      episodes: List['BaseEpisode'],
                      start_source: 'BaseSource',
                      start_video: 'BaseVideo',
                      ) -> Tuple['Video', str]:
    # this hash value helps pick required videos
    base_source_hash = source_hash(start_source)
    for episode in episodes:
        sources = episode.get_sources()
        # pick source
        for source in sources:
            if base_source_hash == source_hash(source):
                break
        else:
            break

        videos = source.get_videos()
        for video in videos:
            if video == start_video:
                title = create_player_title(episode, source, anime)
                yield video, title


@contextmanager
def new_tmp_playlist(playlist_raw: str) -> str:
    """used for make temp playlist for playing videos"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u') as temp_file:
        temp_file.write(playlist_raw)
    try:
        yield temp_file.name
    finally:
        temp_file.close()
