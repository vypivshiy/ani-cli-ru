from typing import TYPE_CHECKING, List

from .cached_extractor import CachedExtractor, CachedExtractorAsync, CachedItemAsyncContext, CachedItemContext

if TYPE_CHECKING:
    from anicli_api.base import Video


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
