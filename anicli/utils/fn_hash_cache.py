"""helper hash functions for storage extracted dataclasses from anicli-api"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anicli_api.base import BaseExtractor


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
