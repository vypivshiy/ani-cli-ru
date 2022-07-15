from __future__ import annotations

import warnings
import re
from html import unescape
from typing import Optional, Dict, Pattern, Sequence, Union, List, TypedDict, Tuple

from requests import Response

from anicli_ru._http import client
from anicli_ru import Kodik, Aniboom

__all__ = ("BaseAnimeHTTP",
           "BaseParser",
           "BaseJsonParser",
           "BaseAnimeResult",
           "BasePlayer",
           "BaseEpisode",
           "BaseOngoing",
           "ResultList")


class TESTS(TypedDict):
    """ Dict for testing extractors

    search: title_name: str, episodes: int - check search method and get episodes

    ongoing: bool - check ongoings search

    video: bool - test get video url

    search_blocked: bool - ignore failed get episode and retry get episodes for non blocked title

    search_not_found: str title - this title has not exist

    instant: str - title, where need get all video urls

    """
    search: Tuple[str, int]
    ongoing: bool
    video: bool
    search_blocked: bool
    search_not_found: str
    instant: str


class BaseAnimeHTTP:
    """Base singleton class for send request to url, where need get html/json documents.

    the following variables and methods should be overridden in this class:

    BASE_URL: - main url site

    def search(self, q: str): - search by string

    def ongoing(self, *args, **kwargs): - search ongoings

    def episodes(self, *args, **kwargs): - search episodes

    def players(self, *args, **kwargs): - search direct video url

    _TESTS: - config dict for testing extractor

    Optional:

        USER_AGENT: - Useragent. In CLI, default set random by utils.random_agent module


    """
    BASE_URL = "https://example.com/"
    # XMLHttpRequest value required!
    USER_AGENT = {
        "user-agent":
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
            "x-requested-with": "XMLHttpRequest"}
    _instance = None
    TIMEOUT: float = 30
    # dict for get parser config tests
    _TESTS: TESTS = {
        "search": ("experiments lain", 13),  # standard search test
        "ongoing": True,  # test search ongoings, True - yes, False - no
        "video": True,  # test get raw video, True - yes, False - no
        "search_blocked": False,  # ignore failed get episode and retry get episodes for non blocked title
        "search_not_found": "_thisTitleIsNotExist123456",  # this title has not exist
        "instant": "experiments lain"  # test instant key scroll series
    }
    # костыль для настройки поведения ключа INSTANT issue #6:
    # если сначала идёт выбор озвучки, а потом плеера, выставите значение True (see extractors/animego)
    INSTANT_KEY_REPARSE = False

    def __new__(cls, *args, **kwargs):
        # create singleton for correct store session
        if not cls._instance:
            cls._instance = super(BaseAnimeHTTP, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.session = client
        self.session.timeout = self.TIMEOUT
        self.session.headers.update(self.USER_AGENT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    # def request(self, method: str, url: str, **kwargs) -> Response:
    #     """Session.request method
    #
    #     :param str method: method type
    #     :param str url: url target
    #     :param kwargs: optional requests.Session kwargs
    #     :return: requests.Response object
    #     """
    #     # context manager solve ResourceWarning (trace this in tests)
    #     warnings.warn("Usage self.session.request method in parsers", category=SyntaxWarning, stacklevel=2)
    #     with self.session as s:
    #         return s.request(method, url, timeout=self.TIMEOUT, **kwargs)
    #
    # def request_get(self, url: str, **kwargs) -> Response:
    #     """Session.get method
    #
    #     :param str url: url target
    #     :param kwargs: optional requests.Session kwargs
    #     :return: requests.Response object
    #     """
    #     warnings.warn("Usage self.session.get method in parsers", category=SyntaxWarning, stacklevel=2)
    #     return self.request("GET", url, **kwargs)
    #
    # def request_post(self, url: str, **kwargs) -> Response:
    #     """Session.post method
    #
    #     :param url: url target
    #     :param kwargs: optional requests.Session kwargs
    #     :return: requests.Response object
    #     """
    #     warnings.warn("Usage self.session.post method in parsers", category=SyntaxWarning, stacklevel=2)
    #     return self.request("POST", url, **kwargs)

    # need manually write requests in parsers with self.session object

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        """Search anime title by string pattern

        :param str q: string search
        :return: list with AnimeResult objects
        """
        raise NotImplementedError

    def ongoing(self, *args, **kwargs) -> ResultList[BaseOngoing]:
        """Search ongoings

        :param args:
        :param kwargs:
        :return: list with Ongoing objects
        """
        raise NotImplementedError

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]:  # type: ignore
        """

        :param args:
        :param kwargs:
        :return: list with Episode objects
        """
        raise NotImplementedError

    def episode_reparse(self, *args, **kwargs):
        """Need write this method if INSTANT_KEY_REPARSE == True (see, extractors/animego.py)

        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:  # type: ignore
        """

        :param args:
        :param kwargs:
        :return: list with Player objects
        """
        raise NotImplementedError

    def get_kodik_video(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Get hls url from kodik balancer

        :param str player_url: - raw url from kodik balancer
        :param int quality: - video quality. Default 720
        :param str referer: - referer, where give this url. Default get automatically
        :return: direct video url
        """
        return Kodik()(player_url, quality, referer=referer)

    def get_aniboom_video(self, player_url: str, quality: int = 1080) -> str:
        """get hls url from aniboom balancer

        :param player_url: raw url from aniboom balancer
        :return: direct video url
        """
        # fix 28 11 2021 request
        referer = self.BASE_URL if self.BASE_URL.endswith("/") else f"{self.BASE_URL}/"
        return Aniboom().get_video_url(player_url, referer=referer, quality=quality)

    def get_video(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Get video from balancer. Check balancer, where from url

        :param player_url: player url from any balancer
        :param quality: video quality. Default 720
        :param referer: referer string. Default set automatically
        :return:
        """
        if "sibnet" in player_url:
            return player_url
        elif Aniboom.is_aniboom(player_url):
            url = self.get_aniboom_video(player_url, quality=quality)
            return url
        elif Kodik.is_kodik(player_url):
            url = self.get_kodik_video(player_url, quality, referer=referer)
            return url
        else:
            # catch any players for add in script
            raise TypeError(f"The link {player_url} is not defined by the available balancers.")


# old alias
ResultList = List


class BaseParser:
    """Base object parser from text response

    REGEX: Dict[key: str, value: Pattern] - a dictionary with keys, and
    re.compile expressions values, which the parser will get and assign to objects

    re.compile expression must extract **one group value** from the document for the default parser to work correctly.

    If this is not the case, then you must redefine the logic of the parse classmethod
    """

    REGEX: Dict[str, Pattern]  # {"attr_name": re.compile(<regular expression>)}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = int(v) if v.isdigit() else unescape(str(v))
            setattr(self, k, v)

    @classmethod
    def parse(cls, html: str) -> ResultList:
        """class object factory

        :param str html: html document
        :return: ResultList with objects
        """
        l_objects = []
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}
        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            l_objects.append(cls(**dict(attrs)))
        return l_objects


class BaseJsonParser:
    """Base parser object for JSON response (see extractors/anilibria.py)

    KEYS: Sequence - collection of keys to get from json"""
    REGEX = None
    KEYS: Sequence[str]

    @classmethod
    def parse(cls, response: Union[Dict, List]) -> ResultList:
        """class object factory

        :param response: json response
        :return: ResultList with objects
        """
        rez = []
        if isinstance(response, list):
            for data in response:
                c = cls()
                for k in data.keys():
                    if k in cls.KEYS:
                        setattr(c, k, data[k])
                rez.append(c)
        elif isinstance(response, dict):
            c = cls()
            for k in response.keys():
                if k in cls.KEYS:
                    setattr(c, k, response[k])
            rez.append(c)
        return rez


BaseParserObject = BaseParser  # old alias


class BasePlayer(BaseParserObject):
    """Player object class. Contains balancer url and method get video url

    """
    ANIME_HTTP: BaseAnimeHTTP
    dub_name: str
    _player: str

    @property
    def url(self) -> str:
        """get player url"""
        return self.player_prettify(self._player)

    @staticmethod
    def player_prettify(player: str):
        """Player prettify url method and convert all named and numeric character references
        (e.g. &gt;, &#62;, &x3e;) in the string to the corresponding unicode characters:


        //foobar.com/barfoo12345 -> https://foobar.com/barfoo12345


        :param str player: - raw player url
        :return:
        """
        return f"https:{unescape(player)}"

    def get_video(self, quality: int = 720, referer: Optional[str] = None) -> str:
        """Get direct video url

        :param int quality: video quality. Default 720
        :param referer: referer string. Default set auto.
        :return: video url
        """
        if not referer:
            referer = self.ANIME_HTTP.BASE_URL if self.ANIME_HTTP.BASE_URL.endswith("/") else f"{self.ANIME_HTTP.BASE_URL}/"

        with self.ANIME_HTTP as a:
            return a.get_video(player_url=self.url, quality=quality, referer=referer)


class BaseEpisode(BaseParserObject):
    ANIME_HTTP: BaseAnimeHTTP

    def player(self) -> ResultList[BasePlayer]:
        """Get list with Player object

        :return: ResultList with Player objects
        """
        with self.ANIME_HTTP as a:
            return a.players(self)


class BaseOngoing(BaseParserObject):
    ANIME_HTTP: BaseAnimeHTTP
    url: str
    title: str

    def episodes(self) -> ResultList[BaseEpisode]:
        """Get list with Episode objects

        :return: ResultList with Episode objects
        """
        with self.ANIME_HTTP as a:
            return a.episodes(self)


class BaseAnimeResult(BaseParserObject):
    ANIME_HTTP: BaseAnimeHTTP
    url: str
    title: str

    def episodes(self) -> ResultList[BaseEpisode]:
        """Get list with Episode objects

        :return: ResultList with Episode objects
        """
        with self.ANIME_HTTP as a:
            return a.episodes(self)
