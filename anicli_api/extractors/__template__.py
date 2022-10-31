"""Template extractor

"""
from typing import List, TypeVar # for python 3.8 support typehint

from anicli_api.extractors.base import (
    AnimeExtractor,
    BaseSearchResult,
    BaseEpisode,
    BaseOngoing,
    BaseAnimeInfo,
    BaseVideo,
    BaseModel,
    T_Ongoing,
    T_Search, TypeOngoing, TypeSearch
)


T_Base = TypeVar("T_Base", bound=BaseModel)


class Extractor(AnimeExtractor):

    def search(self, query: str) -> List[TypeSearch]:
        pass

    def ongoing(self) -> List[TypeOngoing]:
        pass

    async def async_search(self, query: str) -> List[TypeSearch]:
        pass

    async def async_ongoing(self) -> List[TypeOngoing]:
        pass


class SearchResult(BaseSearchResult):
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class Ongoing(BaseOngoing):
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    async def a_get_episodes(self) -> List['Episode']:
        # past async code here
        pass

    def get_episodes(self) -> List['Episode']:
        # past code here
        pass


class Episode(BaseEpisode):
    async def a_get_videos(self) -> List['Video']:
        # past async code here
        pass

    def get_videos(self) -> List['Video']:
        # past code here
        pass


class Video(BaseVideo):
    # optional past metadata attrs here
    pass
