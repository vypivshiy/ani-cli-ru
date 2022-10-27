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
from typing import Union, Dict, Any, List
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

    def search(self, query: str):
        raise NotImplementedError

    def ongoing(self):
        raise NotImplementedError

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

    def get_anime(self):
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

    def get_anime(self):
        """return BaseAnimeInfo object"""
        raise NotImplementedError


class BaseEpisode(BaseModel):
    def get_videos(self):
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

    def get_episodes(self):
        """return List[Episodes] objects"""
        raise NotImplementedError


class BaseVideo(BaseModel):
    """Base video class object.

    minimum required attributes:

    url: str - url to balancer or direct video
    """
    url: str

    def get_source(self):
        """if video is Kodik or Aniboom, return dict with videos. Else, return direct url"""
        if self.url == Kodik():
            return Kodik.parse(self.url)
        elif self.url == Aniboom():
            return Aniboom.parse(self.url)
        return self.url
