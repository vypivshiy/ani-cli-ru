from __future__ import annotations
from requests import Session
from collections import UserList
from html.parser import unescape
from .utils import kodik_decoder
import re

# aniboom regular expressions (work after unescape response html page)
RE_ANIBOOM = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')

# kodik/anivod regular expressions
RE_KODIK_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
RE_KODIK_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
RE_KODIK_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
RE_KODIK_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
RE_KODIK_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")


class ListObj(UserList):
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


class BaseObj:
    """base object for responses"""
    REGEX: dict  # {"attr_name": re.compile(<regular expression>)}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = int(v) if v.isdigit() else unescape(str(v))
            setattr(self, k, v)

    @classmethod
    def parse(cls, html: str) -> ListObj:
        """class object factory"""
        l_objects = ListObj()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}
        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            l_objects.append(cls(**dict(attrs)))
        return l_objects


class BaseAnime:
    BASE_URL = "your_base_source_link"
    # mobile user-agent can sometimes gives a chance to bypass the anime title ban
    USER_AGENT = {
        "user-agent":
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
            "x-requested-with": "XMLHttpRequest"}
    _instance = None

    def __new__(cls, *args, **kwargs):
        # singleton for correct store session
        if not cls._instance:
            cls._instance = super(BaseAnime, cls).__new__(
                cls, *args, **kwargs)
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
        return

    def request(self, method, url, **kwargs):
        return self.session.request(method, url, **kwargs)

    def request_get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def search(self, q: str):
        raise NotImplementedError

    def ongoing(self, *args, **kwargs):
        raise NotImplementedError

    def episodes(self, *args, **kwargs):
        raise NotImplementedError

    def players(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _get_kodik_payload(resp: str, referer: str) -> tuple[dict, str]:
        # prepare values for next POST request
        url_data, = re.findall(RE_KODIK_URL_DATA, resp)
        type_, = re.findall(RE_KODIK_VIDEO_TYPE, url_data)
        id_, = re.findall(RE_KODIK_VIDEO_ID, url_data)
        hash_, = re.findall(RE_KODIK_VIDEO_HASH, url_data)
        data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", 1)[1].split("&")}
        data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                     "ref": referer.rstrip("/")})
        return data, url_data

    def get_kodik_url(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Get hls url in kodik/anivod player"""
        quality_available = (720, 480, 360, 240, 144)
        if quality not in quality_available:
            quality = 720
        quality = str(quality)

        resp = self.request_get(player_url, headers=self.USER_AGENT.copy().update({"referer": referer}))

        data, url_data = self._get_kodik_payload(resp.text, referer)
        # kodik server regular expr detection
        if not RE_KODIK_URL.match(player_url):
            raise TypeError(
                f"Unknown player balancer. get_kodik_url method support kodik and anivod players\nvideo url: {player_url}")

        url_, = RE_KODIK_URL.findall(player_url)
        url = f"https://{url_}/gvi"
        resp = self.request("POST", url, data=data,
                            headers=self.USER_AGENT.copy().update({"referer": f"https://{url_data}",
                                                                   "orgign": url.replace("/gvi", ""),
                                                                   "accept":
                                                                       "application/json, text/javascript, */*; q=0.01"
                                                                   })).json()["links"]
        video_url = resp["480"][0]["src"]
        video_url = kodik_decoder(video_url).replace("480.mp4", f"{quality}.mp4")
        return video_url

    def get_aniboom_url(self, player_url: str) -> str:
        """get aniboom video"""
        # fix 28 11 2021 request
        r = self.request_get(
            player_url,
            headers={
                "referer": "https://animego.org/",
                "user-agent":
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                    "Safari/537.36"})

        r = unescape(r.text)
        return re.findall(RE_ANIBOOM, r)[0].replace("\\", "")

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
        elif RE_KODIK_URL.match(player_url):
            url = self.get_kodik_url(player_url, quality, referer=referer)
            return url
        else:
            # catch any players for add in script
            print("Warning!", player_url, "is not supported!")
