"""Template extractor

"""
from typing import List

from anicli_api.extractors.base import (
    AnimeExtractor,
    BaseSearchResult,
    BaseEpisode,
    BaseOngoing,
    BaseAnimeInfo,
    BaseVideo,
    BaseModel
)


class Extractor(AnimeExtractor):
    async def a_search(self, query: str) -> List['SearchResult']:
        pass

    async def a_ongoing(self) -> List['Ongoing']:
        pass

    def search(self, query: str) -> List['SearchResult']:
        # past code here
        ...

    def ongoing(self) -> List['Ongoing']:
        # past code here
        ...


class SearchResult(BaseSearchResult):
    async def a_get_anime(self) -> 'AnimeInfo':
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class Ongoing(BaseOngoing):
    async def a_get_anime(self) -> 'AnimeInfo':
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    async def a_get_episodes(self) -> List['Episode']:
        pass

    def get_episodes(self) -> List['Episode']:
        # past code here
        ...


class Episode(BaseEpisode):
    async def a_get_videos(self) -> List['Video']:
        pass

    def get_videos(self) -> List['Video']:
        # past code here
        ...


class Video(BaseVideo):
    url: str
    ...
