"""Template extractor

"""
from anicli_api.extractors.base import *

__all__ = (
    'Extractor',
    'SearchResult',
    'Ongoing',
    'AnimeInfo',
    'Episode',
    'Video',
    'TestCollections'
)


class Extractor(BaseAnimeExtractor):
    # optional constants, HTTP configuration here
    def search(self, query: str) -> List[BaseSearchResult]:
        # past code here
        pass

    def ongoing(self) -> List[BaseOngoing]:
        # past code here
        pass

    async def async_search(self, query: str) -> List[BaseSearchResult]:
        # past async code here
        pass

    async def async_ongoing(self) -> List[BaseOngoing]:
        # past async code here
        pass


class SearchResult(BaseSearchResult):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class Ongoing(BaseOngoing):
    # optional past metadata attrs here
    async def a_get_anime(self) -> 'AnimeInfo':
        # past async code here
        pass

    def get_anime(self) -> 'AnimeInfo':
        # past code here
        pass


class AnimeInfo(BaseAnimeInfo):
    # optional past metadata attrs here
    async def a_get_episodes(self) -> List['BaseEpisode']:
        # past async code here
        pass

    def get_episodes(self) -> List['BaseEpisode']:
        # past code here
        pass


class Episode(BaseEpisode):
    # optional past metadata attrs here
    async def a_get_videos(self) -> List['BaseVideo']:
        # past async code here
        pass

    def get_videos(self) -> List['BaseVideo']:
        # past code here
        pass


class Video(BaseVideo):
    # optional past metadata attrs here
    pass


class TestCollections(BaseTestCollections):
    def test_search(self):
        pass

    def test_ongoing(self):
        pass

    def test_extract_metadata(self):
        pass

    def test_extract_video(self):
        pass
