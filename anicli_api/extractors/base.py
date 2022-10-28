"""base prototype architecture for anicli extractor

Extractor works schema:
    [Extractor]------------------download TODO add standard work implementation for download method
        | search()/ongoing()        |
        V                           |
  [SearchResult | Ongoing]          |
         | anime()                  |
         V                          |
    [AnimeInfo]                     |
        | episodes()                 |
        V                           |
    [Episodes]                      |
        | videos()                   |
        V                           |
    [Video] <-----------------------

"""
from typing import Union, Dict, Any, List, Generator
from html import unescape

from bs4 import BeautifulSoup

from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many
from anicli_api._http import BaseHTTPSync, BaseHTTPAsync
from anicli_api.decoders import Kodik, Aniboom


class AnimeExtractor:
    """First extractor entrypoint class"""
    HTTP = BaseHTTPSync()
    ASYNC_HTTP = BaseHTTPAsync()

    _ReField = ReField
    _ReFieldList = ReFieldList
    _ReFieldListDict = ReFieldListDict
    _parse_many = parse_many

    @staticmethod
    def _iter_from_result(obj: Union['BaseSearchResult', 'BaseOngoing']):
        # TODO add __iter__ magic methods in objects
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
    async def _aiter_from_result(obj: Union['BaseSearchResult', 'BaseOngoing']):
        # TODO add __aiter__ magic methods in objects
        anime = await obj.a_get_anime()
        for episode in (await anime.a_get_episodes()):
            for video in (await episode.a_get_videos()):
                yield {
                    "search": obj.dict(),
                    "anime": anime.dict(),
                    "episode": episode.dict(),
                    "video_meta": video.dict(),
                    "video": video.get_source()}

    def search(self, query: str) -> List['BaseSearchResult']:
        raise NotImplementedError

    def iter_search(self, query: str) -> Generator[Dict[str, Any], None, None]:
        for search_result in self.search(query):
            yield from self._iter_from_result(search_result)

    def ongoing(self) -> List['BaseOngoing']:
        raise NotImplementedError

    def iter_ongoing(self) -> Generator[Dict[str, Any], None, None]:
        for ongoing in self.ongoing():
            yield from self._iter_from_result(ongoing)

    async def a_search(self, query: str) -> List['BaseSearchResult']:
        raise NotImplementedError

    async def aiter_search(self, query: str) -> Generator[Dict[str, Any], None, None]:
        # TODO add __aiter__, __iter__ magic methods in objects
        for search_result in (await self.a_search(query)):
            async for data in self._aiter_from_result(search_result):
                yield data

    async def a_ongoing(self) -> List['BaseOngoing']:
        raise NotImplementedError

    async def aiter_ongoing(self) -> Generator[Dict[str, Any], None, None]:
        # TODO add __aiter__, __iter__ magic methods in objects
        for ongoing in (await self.a_ongoing()):
            async for data in self._aiter_from_result(ongoing):
                yield data

    @staticmethod
    def _soup(markup: Union[str, bytes], *, parser: str = "html.parser", **kwargs) -> BeautifulSoup:
        """return BeautifulSoup instance"""
        return BeautifulSoup(markup, parser, **kwargs)

    @staticmethod
    def _unescape(text: str) -> str:
        """equal html.unescape"""
        return unescape(text)


class BaseModel:
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
        """return BeautifulSoup instance"""
        return BeautifulSoup(markup, parser, **kwargs)

    @staticmethod
    def _unescape(text: str) -> str:
        """equal html.unescape"""
        return unescape(text)

    def dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__annotations__
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

    async def a_get_anime(self) -> 'BaseAnimeInfo':
        raise NotImplementedError

    def get_anime(self) -> 'BaseAnimeInfo':
        """return BaseAnimeInfo object"""
        raise NotImplementedError


class BaseOngoing(BaseSearchResult):
    """Base ongoing class object.

    required attributes:

    url: str - url to main title page

    title: str - anime title name

    num: int - episode number"""
    url: str
    name: str
    num: int

    async def a_get_anime(self) -> 'BaseAnimeInfo':
        raise NotImplementedError

    def get_anime(self) -> 'BaseAnimeInfo':
        """return BaseAnimeInfo object"""
        raise NotImplementedError


class BaseEpisode(BaseModel):

    async def a_get_videos(self) -> List['BaseVideo']:
        raise NotImplementedError

    def get_videos(self) -> List['BaseVideo']:
        """return List[BaseVideo] objects"""
        raise NotImplementedError


class BaseAnimeInfo(BaseModel):
    # id: str
    # url: str
    # name: str
    # alt_names: List[str]
    # status: str
    # images: List[str]
    # type: str  # tv, episodes, etc
    # series: int
    # length: str
    # genres: List[str]
    # season: str

    async def a_get_episodes(self) -> List['BaseEpisode']:
        raise NotImplementedError

    def get_episodes(self) -> List['BaseEpisode']:
        """return List[Episodes] objects"""
        raise NotImplementedError


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
