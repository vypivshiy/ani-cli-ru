from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Type, TypedDict

from anicli_api.base import BaseAnime, BaseEpisode, BaseExtractor, BaseOngoing, BaseSearch, BaseSource
from anicli_api.player.base import Video


# main app context
class AnicliContext(TypedDict, total=False):
    # internal app fields (late init)

    # TODO
    app_version: str
    api_version: str
    config_path: Path
    extractor_instance: Type[BaseExtractor]
    extractor: BaseExtractor

    # config fields (cli args/read config)
    extractor_name: str
    quality: int
    mpv_opts: str
    m3u_size: int
    proxy: Optional[str]
    cookies: Optional[CookieJar]
    headers: Dict[str, str]
    timeout: int


# ongoing context
class OngoingContext(TypedDict, total=False):
    # initial via command
    results: Sequence[BaseOngoing]
    default_quality: int
    mpv_opts: str
    m3u_size: int

    # step_1
    result_num: int

    # step_2
    anime: BaseAnime
    episodes: Sequence[BaseEpisode]
    # single or slice play
    episodes_num: int
    episodes_mask: List[bool]

    # step_3
    sources: Sequence[BaseSource]
    source_num: int

    # auto get by default_quality
    videos: Sequence[Video]
    video_num: int


# search context
class SearchContext(TypedDict, total=False):
    # initial via command
    query: str
    results: Sequence[BaseSearch]
    default_quality: int
    mpv_opts: str
    m3u_size: int

    # step_1
    result_num: int

    # step_2
    anime: BaseAnime
    episodes: Sequence[BaseEpisode]
    # single or slice play
    episodes_num: int
    episodes_mask: List[bool]

    # step_3
    sources: Sequence[BaseSource]
    source_num: int
    # auto get by default_quality
    videos: Sequence[Video]
    video_num: int
