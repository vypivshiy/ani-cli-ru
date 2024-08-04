"""extractor hash wrapper helps anicli-api extractors storage extracted objects """
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor, BaseAnime, BaseEpisode, BaseSource

from cachetools import TTLCache
from asyncache import cached

from ..types_ import SEARCH_OR_ONGOING

DEFAULT_TTL_CACHE_TIME = timedelta(minutes=10).seconds
LRU_CACHE_INSTANCE = TTLCache(ttl=DEFAULT_TTL_CACHE_TIME, maxsize=1024 * 32)


def _hash_search(e: 'BaseExtractor', query: str) -> int:
    return hash((e.BASE_URL, query))


def _hash_ongoing(e: 'BaseExtractor') -> int:
    return hash((e.BASE_URL, 'ONGOING'))


def _hash_anime(e: 'BaseExtractor', item: 'SEARCH_OR_ONGOING') -> int:
    # animevost, anilibra API hash patch via frozenset (thumbnail is dict)
    return hash((e.BASE_URL, item.url, item.title, frozenset(item.thumbnail)))


def _hash_episode(e: 'BaseExtractor', item: 'BaseAnime') -> int:
    # animevost, anilibra API hash patch via frozenset (thumbnail is dict)
    return hash((e.BASE_URL, item.title, item.description, frozenset(item.thumbnail)))


def _hash_sources(e: 'BaseExtractor', item: 'BaseEpisode') -> int:
    return hash((e.BASE_URL, item.title, item.num))


def _hash_videos(e: 'BaseExtractor', item: 'BaseSource') -> int:
    return hash((e.BASE_URL, item.title, item.url))


class CachedExtractor:
    def __init__(self, extractor: 'BaseExtractor'):
        self.extractor = extractor

    @property
    def BASE_URL(self):
        return self.extractor.BASE_URL

    @cached(LRU_CACHE_INSTANCE, _hash_search)
    async def a_search(self, query: str):
        return await self.extractor.a_search(query)

    @cached(LRU_CACHE_INSTANCE, _hash_ongoing)
    async def a_ongoing(self):
        return await self.extractor.a_ongoing()

    @cached(LRU_CACHE_INSTANCE, _hash_anime)
    async def a_get_anime(self, item: SEARCH_OR_ONGOING):
        return await item.a_get_anime()

    @cached(LRU_CACHE_INSTANCE, _hash_episode)
    async def a_get_episodes(self, item: 'BaseAnime'):
        return await item.a_get_episodes()

    @cached(LRU_CACHE_INSTANCE, _hash_sources)
    async def a_get_sources(self, item: 'BaseEpisode'):
        return await item.a_get_sources()

    @cached(LRU_CACHE_INSTANCE, _hash_videos)
    async def a_get_videos(self, item: 'BaseSource'):
        return await item.a_get_videos()

    def __hash__(self):
        return hash(self.extractor.BASE_URL)
