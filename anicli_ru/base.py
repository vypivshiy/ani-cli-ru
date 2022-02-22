from __future__ import annotations
from collections import UserList
import re
from html import unescape

from requests import Session, Response

from .utils.player_tools import kodik_decoder, kodik_parse_payload, is_kodik, get_kodik_url, get_aniboom_url


class BaseAnimeHTTP:
    """Базовый класс-singleton для отправки запросов на сайт, откуда парсить все значения.

    В этом классе должны определенны следующие методы:

    def search(self, q: str): - поиск по строке

    def ongoing(self, *args, **kwargs): - поиск онгоингов

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]: - поиск эпизодов

    def players(self, *args, **kwargs): - поисск ссылок на доступные плееры

    В этом классе должны опеределны следующие аттрибуты:

    BASE_URL: - Основная ссылка, куда будут идти запросы

    USER_AGENT: - Юзерагент, с которым будут идти запросы. Значение **XMLHttpRequest** должно быть обязательно

    """
    BASE_URL = "your_base_source_link"
    # XMLHttpRequest value required!
    USER_AGENT = {
        "user-agent":
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
            "x-requested-with": "XMLHttpRequest"}
    _instance = None
    TIMEOUT: float = 30
    # optional dict for get parser config tests
    _TESTS = {
        "search": ["experiments lain", 13],  # standard search test
        "ongoing": True,  # test search ongoings, True - yes, False - no
        "video": True,  # test get raw video, True - yes, False - no
        "search_blocked": False,  # ignore failed get episode and retry get episodes for non blocked title
        "search_not_found": ["_thisTitleIsNotExist123456"],  # this title has not exist
    }

    def __new__(cls, *args, **kwargs):
        # singleton for correct store session
        if not cls._instance:
            cls._instance = super(BaseAnimeHTTP, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, session: Session = None):
        if session:
            self.session = session
            self.session.headers.update({"x-requested-with": "XMLHttpRequest"})
        else:
            self.session = Session()
            self.session.headers.update(self.USER_AGENT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def request(self, method, url, **kwargs) -> Response:
        # context manager solve ResourceWarning (trace this in tests)
        with self.session as s:
            return s.request(method, url, timeout=self.TIMEOUT, **kwargs)

    def request_get(self, url, **kwargs) -> Response:
        return self.request("GET", url, **kwargs)

    def request_post(self, url, **kwargs) -> Response:
        return self.request("POST", url, **kwargs)

    # need manually write requests

    def search(self, q: str) -> UserList[BaseAnimeResult]:
        raise NotImplementedError

    def ongoing(self, *args, **kwargs) -> UserList[BaseOngoing]:
        raise NotImplementedError

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]:
        raise NotImplementedError

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:
        raise NotImplementedError

    def get_kodik_url(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Get hls url in kodik/anivod player

        :param str player_url: - raw url in kodik balancer
        :param int quality: - video quality. Default 720
        :param str referer: - referer, where give this url
        """
        if quality not in (720, 480, 360):
            quality = 720

        resp = self.request_get(player_url, headers=self.USER_AGENT.copy().update({"referer": referer}))

        data, url_data = kodik_parse_payload(resp.text, referer)
        # kodik server regular expr detection
        if not is_kodik(player_url):
            raise TypeError(
                f"Unknown player balancer. get_kodik_url method support kodik balancer\nvideo url: {player_url}")

        url = get_kodik_url(player_url)
        resp = self.request("POST", url, data=data,
                            headers=self.USER_AGENT.copy().update({"referer": f"https://{url_data}",
                                                                   "orgign": url.replace("/gvi", ""),
                                                                   "accept":
                                                                       "application/json, text/javascript, */*; q=0.01"
                                                                   })).json()["links"]
        video_url = resp["480"][0]["src"]
        # kodik balancer returns max quality 480, but it has (720, 480, 360) values
        video_url = kodik_decoder(video_url).replace("480.mp4", f"{quality}.mp4")
        return video_url

    def get_aniboom_url(self, player_url: str) -> str:
        """get aniboom video"""
        # fix 28 11 2021 request
        if not self.BASE_URL.endswith("/"):
            b_u = self.BASE_URL + "/"
        else:
            b_u = self.BASE_URL
        r = self.request_get(
            player_url,
            headers={
                "referer": b_u,
                "user-agent": self.session.headers["user-agent"]})

        return get_aniboom_url(r.text)

    def get_video(self, player_url: str, quality: int = 720, *, referer: str = ""):
        """Return direct video url

        :param Player player: player object
        :return: direct video url
        """
        if "sibnet" in player_url:
            return player_url
        elif "aniboom" in player_url:
            url = self.get_aniboom_url(player_url)
            return url
        elif is_kodik(player_url):
            url = self.get_kodik_url(player_url, quality, referer=referer)
            return url
        else:
            # catch any players for add in script
            print("Warning!", player_url, "is not supported!")


class ResultList(UserList):
    """Modified list object"""

    def print_enumerate(self, *args):
        """print elements with getattr names arg. Default invoke __str__ method"""
        if len(self) > 0:
            for i, obj in enumerate(self, 1):
                if args:
                    print(f"[{i}]", *(getattr(obj, arg) for arg in args))
                else:
                    print(f"[{i}]", obj)
        else:
            print("Results not founded!")


class BaseParserObject:
    """base object parser for text respons"""
    REGEX: dict  # {"attr_name": re.compile(<regular expression>)}
    # for ide help add attr ex
    # url: str
    # id: int
    # ...

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = int(v) if v.isdigit() else unescape(str(v))
            setattr(self, k, v)

    @classmethod
    def parse(cls, html: str) -> ResultList:
        """class object factory"""
        l_objects = ResultList()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}
        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            l_objects.append(cls(**dict(attrs)))
        return l_objects


class BasePlayer(BaseParserObject):
    url: str

    def get_video(self, quality: int = 720, referer: str = "https://example.com/"):
        raise NotImplementedError


class BaseEpisode(BaseParserObject):
    def player(self) -> UserList[BasePlayer]:
        raise NotImplementedError


class BaseOngoing(BaseParserObject):
    def episodes(self) -> UserList[BaseEpisode]:
        raise NotImplementedError


class BaseAnimeResult(BaseParserObject):
    """"""
    def episodes(self) -> UserList[BaseEpisode]:
        raise NotImplementedError


# old aliases
ListObj = ResultList
BaseObj = BaseParserObject
BaseAnime = BaseAnimeHTTP
