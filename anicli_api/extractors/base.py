"""base prototype architecture for anicli extractor

Extractor works schema:
    [Extractor]------------------download TODO add standard work implementation for download method
        | search()/ongoing()        |
        V                           |
  [SearchResult | Ongoing]          |
         | get_anime()              |
         V                          |
    [AnimeInfo]                     |
        | get_episodes()            |
        V                           |
    [Episodes]                      |
        | get_videos()              |
        V                           |
    [Video] <-----------------------
        |
        V
    {quality: url, ...} or url
"""
from __future__ import annotations

from typing import Union, Dict, Any, List, Generator, Awaitable, AsyncGenerator, TypedDict
from html import unescape

from bs4 import BeautifulSoup

from abc import ABC, abstractmethod
from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many
from anicli_api._http import BaseHTTPSync, BaseHTTPAsync
from anicli_api.decoders import Kodik, Aniboom


__all__ = (
    'BaseModel',
    'BaseOngoing',
    'BaseEpisode',
    'BaseVideo',
    'BaseSearchResult',
    'BaseAnimeInfo',
    'BaseAnimeExtractor',
    'BaseTestCollections',
    'RawData',
    'List'  # python 3.8 support typehint
)


class RawData(TypedDict):
    search: Dict[str, Any]  # Ongoing.dict() | SearchResult.dict()
    anime: Dict[str, Any]  # AnimeInfo.dict()
    episode: Dict[str, Any]  # Episode.dict()
    video_meta: Dict[str, Any]  # Video.dict()
    video: Union[str, Dict[str, Any]]  # Video.get_source()


class BaseModel(ABC):
    """Base Model class

    instances:

    HTTP = BaseHTTPSync() - http singleton sync requests class

    HTTP_ASYNC = BaseHTTPAsync() - http singleton async requests class

    methods:

    BaseModel._soup - return BeautifulSoap instance

    BaseModel._unescape - unescape text

    optional regex search class helpers:

    _ReField - ReField

    _ReFieldList - re_models.ReFieldList

    _ReFieldListDict - re_models.ReFieldListDict

    _parse_many - re_models.parse_many
    """
    # http singleton sync requests class
    HTTP = BaseHTTPSync()
    # http singleton async requests class
    HTTP_ASYNC = BaseHTTPAsync()

    _unescape = unescape

    # optional regex search class helpers
    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def _soup(markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs) -> BeautifulSoup:
        """return BeautifulSoup object"""
        return BeautifulSoup(markup, parser, **kwargs)

    @staticmethod
    async def _async_generator(async_func: Awaitable) -> AsyncGenerator:
        """convert awaitable call to AsyncGenerator"""
        for j in (await async_func):
            yield j

    def dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dict__
                if not k.startswith("_") and not k.endswith("_")}

    def __repr__(self):
        return f"[{self.__class__.__name__}] " + ", ".join((f"{k}={v}" for k, v in self.dict().items()))


class BaseSearchResult(BaseModel):
    """Base search result class object.

    required attributes:

    url: str - url to main title page

    name: str - anime title name

    type: str - anime type: serial, film, OVA, etc"""
    url: str
    name: str
    type: str

    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        """return BaseAnimeInfo object"""
        pass

    def _full_parse(self) -> Generator[RawData, None, None]:
        anime = self.get_anime()
        for episode in anime.get_episodes():
            for video_meta in episode.get_videos():
                video = video_meta.get_source()
                yield {"search": self.dict(),
                       "anime": anime.dict(),
                       "episode": episode.dict(),
                       "video_meta": video_meta.dict(),
                       "video": video}

    async def _async_full_parse(self) -> AsyncGenerator[RawData, None]:
        anime = await self.a_get_anime()  # type: ignore
        for episode in (await anime.a_get_episodes()):
            for video_meta in (await episode.a_get_videos()):
                video = await video_meta.a_get_source()
                yield {"search": self.dict(),
                       "anime": anime.dict(),
                       "episode": episode.dict(),
                       "video_meta": video_meta.dict(),
                       "video": video}

    def __iter__(self):
        return self._full_parse()

    def __aiter__(self):
        return self._async_full_parse()


class BaseOngoing(BaseSearchResult):
    """Base ongoing class object.

    required attributes:

    url: str - url to main title page

    title: str - anime title name

    num: int - episode number"""
    url: str
    name: str
    num: int

    @abstractmethod
    async def a_get_anime(self) -> BaseAnimeInfo:
        pass

    @abstractmethod
    def get_anime(self) -> BaseAnimeInfo:
        """return BaseAnimeInfo object"""
        pass

    def _full_parse(self) -> Generator[RawData, None, None]:
        anime = self.get_anime()
        for episode in anime.get_episodes():
            for video_meta in episode.get_videos():
                video = video_meta.get_source()
                yield {"search": self.dict(),
                       "anime": anime.dict(),
                       "episode": episode.dict(),
                       "video_meta": video_meta.dict(),
                       "video": video}

    async def _async_full_parse(self) -> AsyncGenerator[RawData, None]:
        anime = await self.a_get_anime()
        for episode in (await anime.a_get_episodes()):
            for video_meta in (await episode.a_get_videos()):
                video = await video_meta.a_get_source()
                yield {"search": self.dict(),
                       "anime": anime.dict(),
                       "episode": episode.dict(),
                       "video_meta": video_meta.dict(),
                       "video": video}

    def __iter__(self):
        return self._full_parse()

    def __aiter__(self):
        return self._async_full_parse()


class BaseAnimeInfo(BaseModel):
    @abstractmethod
    async def a_get_episodes(self) -> List[BaseEpisode]:
        pass

    @abstractmethod
    def get_episodes(self) -> List[BaseEpisode]:
        """return List[Episodes] objects"""
        pass

    def __iter__(self):
        return iter(self.get_episodes())

    def __aiter__(self):
        return self._async_generator(self.a_get_episodes())


class BaseEpisode(BaseModel):
    @abstractmethod
    async def a_get_videos(self) -> List[BaseVideo]:
        pass

    @abstractmethod
    def get_videos(self) -> List[BaseVideo]:
        """return List[BaseVideo] objects"""
        pass

    def __iter__(self):
        return iter(self.get_videos())

    def __aiter__(self):
        return self._async_generator(self.a_get_videos())


class BaseVideo(BaseModel):
    """Base video class object.

    minimum required attributes:

    url: str - url to balancer or direct video
    """
    url: str

    async def a_get_source(self) -> Union[Dict[str, Any], str]:
        if self.url == Kodik():
            return await Kodik.async_parse(self.url)
        elif self.url == Aniboom():
            return await Aniboom.async_parse(self.url)
        return self.url

    def get_source(self) -> Union[Dict[str, Any], str]:
        """if video is Kodik or Aniboom, return dict with videos. Else, return direct url"""
        if self.url == Kodik():
            return Kodik.parse(self.url)
        elif self.url == Aniboom():
            return Aniboom.parse(self.url)
        return self.url


class BaseAnimeExtractor(ABC):
    """First extractor entrypoint class"""
    HTTP = BaseHTTPSync()
    ASYNC_HTTP = BaseHTTPAsync()

    _unescape = unescape

    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    @abstractmethod
    def search(self, query: str) -> List[BaseSearchResult]:
        pass

    @abstractmethod
    def ongoing(self) -> List[BaseOngoing]:
        pass

    @abstractmethod
    async def async_search(self, query: str) -> List[BaseSearchResult]:
        pass

    @abstractmethod
    async def async_ongoing(self) -> List[BaseOngoing]:
        pass

    @staticmethod
    def _iter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> Generator[RawData, None, None]:
        anime = obj.get_anime()
        for episode in anime.get_episodes():
            for video in episode.get_videos():
                yield {
                    "search": obj.dict(),
                    "anime": anime.dict(),
                    "episode": episode.dict(),
                    "video_meta": video.dict(),
                    "video": video.get_source()}

    @staticmethod
    async def _aiter_from_result(obj: Union[BaseSearchResult, BaseOngoing]) -> AsyncGenerator[RawData, None]:
        anime = await obj.a_get_anime()
        for episode in (await anime.a_get_episodes()):
            for video in (await episode.a_get_videos()):
                yield {
                    "search": obj.dict(),
                    "anime": anime.dict(),
                    "episode": episode.dict(),
                    "video_meta": video.dict(),
                    "video": video.get_source()}

    def walk_search(self, query: str) -> Generator[RawData, None, None]:
        for search_result in self.search(query):
            yield from self._iter_from_result(search_result)

    def walk_ongoing(self) -> Generator[RawData, None, None]:
        for ongoing in self.ongoing():
            yield from self._iter_from_result(ongoing)

    async def async_walk_search(self, query: str) -> AsyncGenerator[RawData, None]:
        for search_result in (await self.async_search(query)):
            async for data in self._aiter_from_result(search_result):
                yield data

    async def async_walk_ongoing(self) -> AsyncGenerator[RawData, None]:
        for ongoing in (await self.async_ongoing()):
            async for data in self._aiter_from_result(ongoing):
                yield data

    @staticmethod
    def _soup(markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs) -> BeautifulSoup:
        """return BeautifulSoup instance"""
        return BeautifulSoup(markup, parser, **kwargs)


class BaseTestCollections(ABC):
    @abstractmethod
    def test_search(self):
        ...

    @abstractmethod
    def test_ongoing(self):
        ...

    @abstractmethod
    def test_extract_metadata(self):
        ...

    @abstractmethod
    def test_extract_video(self):
        ...
