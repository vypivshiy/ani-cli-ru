"""extractor wrapper helps anicli-api cache extracted objects"""
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, List

from .fn_hash_cache import _hash_search, _hash_ongoing, _hash_anime, _hash_episode, _hash_sources, _hash_videos

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor, BaseAnime, BaseEpisode, BaseSource, Video

from cachetools import TTLCache
from asyncache import cached

from ..types_ import SEARCH_OR_ONGOING

DEFAULT_TTL_CACHE_TIME = timedelta(minutes=10).seconds
LRU_CACHE_INSTANCE = TTLCache(ttl=DEFAULT_TTL_CACHE_TIME, maxsize=1024 * 32)


@dataclass
class CachedItemContext:
    """structure for contains picked items states

    used for provide all metadata to video player
    """
    extractor: 'CachedExtractor'
    searches_or_ongoings: list[SEARCH_OR_ONGOING] = field(default_factory=list)
    anime: Optional['BaseAnime'] = None
    episodes: list['BaseEpisode'] = field(default_factory=list)
    sources: list['BaseSource'] = field(default_factory=list)
    videos: list['Video'] = field(default_factory=list)

    # slice variables helpers
    picked_episode_indexes: list[int] = field(default_factory=list)
    picked_source: Optional['BaseSource'] = None
    picked_video: Optional['Video'] = None

    async def a_search(self, query: str):
        self.searches_or_ongoings = await self.extractor.a_search(query)
        return self.searches_or_ongoings

    async def a_ongoing(self):
        self.searches_or_ongoings = await self.extractor.a_ongoing()
        return self.searches_or_ongoings

    async def a_get_anime(self, index: int) -> 'BaseAnime':
        if not self.searches_or_ongoings:
            raise AttributeError('Should be a call a_search or a_ongoing from CachedExtractor first')

        item = self.searches_or_ongoings[index]
        self.anime = await self.extractor.a_get_anime(item)
        return self.anime

    async def a_get_episodes(self) -> List['BaseEpisode']:
        if not self.anime:
            raise AttributeError('Should be a call a_anime from CachedExtractor first')
        self.episodes = await self.extractor.a_get_episodes(self.anime)
        return self.episodes

    async def a_get_sources(self, index: int) -> List['BaseSource']:
        if not self.episodes:
            raise AttributeError('Should be a call a_episodes from CachedExtractor first')
        self.sources = await self.extractor.a_get_sources(self.episodes[index])
        return self.sources

    async def a_get_videos(self, index: int) -> List['Video']:
        if not self.sources:
            raise AttributeError('Should be a call a_sources from CachedExtractor first')
        self.videos = await self.extractor.a_get_videos(self.sources[index])
        return self.videos


class CachedExtractor:
    def __init__(self, extractor: 'BaseExtractor'):
        self.extractor = extractor

    @property
    def BASE_URL(self):
        return self.extractor.BASE_URL

    @cached(LRU_CACHE_INSTANCE, _hash_search)
    async def a_search(self, query: str) -> List[SEARCH_OR_ONGOING]:
        return await self.extractor.a_search(query)

    @cached(LRU_CACHE_INSTANCE, _hash_ongoing)
    async def a_ongoing(self) -> List[SEARCH_OR_ONGOING]:
        return await self.extractor.a_ongoing()

    @cached(LRU_CACHE_INSTANCE, _hash_anime)
    async def a_get_anime(self, item: SEARCH_OR_ONGOING) -> 'BaseAnime':
        return await item.a_get_anime()

    @cached(LRU_CACHE_INSTANCE, _hash_episode)
    async def a_get_episodes(self, item: 'BaseAnime') -> List['BaseEpisode']:
        return await item.a_get_episodes()

    @cached(LRU_CACHE_INSTANCE, _hash_sources)
    async def a_get_sources(self, item: 'BaseEpisode') -> List['BaseSource']:
        return await item.a_get_sources()

    @cached(LRU_CACHE_INSTANCE, _hash_videos)
    async def a_get_videos(self, item: 'BaseSource') -> List['Video']:
        return await item.a_get_videos()

    def __hash__(self):
        return hash(self.extractor.BASE_URL)
