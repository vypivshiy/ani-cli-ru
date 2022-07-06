"""Kodik module utils"""
import warnings
from base64 import b64decode
import re
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    from html.parser import unescape
except ImportError:
    from html import unescape

from requests import Session

from anicli_ru._http import client
from anicli_ru.utils import Agent


class Kodik:
    """Class for parse video from kodik balancer

        Example::
            >>> from anicli_ru.utils import Kodik
            >>> video = Kodik.parse("https://kodik.info/seria/123/hashfoobar123/720p", referer="kodik.info")

        Or with init this class::
            >>> from anicli_ru.utils import Kodik
            >>> k = Kodik()
            >>> k.parse("https://kodik.info/seria/123/hashfoobar123/720p")
            >>> k("https://kodik.info/seria/123/hashfoobar123/720p")
    """
    # kodik/anivod etc regular expressions
    RE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
    RE_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
    RE_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
    RE_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
    RE_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")
    QUALITY = (720, 480, 360)

    def __init__(self, session: Optional[Session] = None):
        if session:
            self.session = session
            self.useragent = self.session.headers.get("user-agent")
        else:
            self.session = Session()
            self.useragent = Agent.desktop()

    def get_video_url(self, player_url: str, quality: int = 720, *, referer: str = ""):
        warnings.warn("Usage Kodik.parse() or Kodik()(...) methods", category=DeprecationWarning, stacklevel=2)
        return self(player_url, quality, referer=referer)

    @staticmethod
    def decode(url_encoded: str) -> str:
        """kodik player video url decoder (reversed base64 string)

        :param str url_encoded: encoded url
        :return: decoded video url"""
        url_encoded = url_encoded[::-1]
        if not url_encoded.endswith("=="):
            url_encoded += "=="
        link = b64decode(url_encoded).decode()
        if not link.startswith("https"):
            link = f"https:{link}"
        return link

    @staticmethod
    def is_kodik(url: str) -> bool:
        """return True if url player is kodik"""
        return bool(Kodik.RE_URL.match(url))

    @classmethod
    def parse(cls,
              kodik_player_url: str,
              quality: int = 720,
              *,
              referer: Optional[str] = None,
              session: Optional[Session] = None,
              raw_response: Optional[str] = None) -> str:
        """
        Class method for get kodik video

        :param kodik_player_url: start kodik player url
        :param quality: video quality. Default None
        :param referer: base source referer. Default None
        :param session: Session object. default config auto
        :param raw_response: raw response from kodik_player_url object. Default none
        :return: direct video url
        """
        if not cls.is_kodik(kodik_player_url):
            raise TypeError(
                f"Unknown player balancer. get_video_url method support kodik balancer\nvideo url: {kodik_player_url}")
        if not referer:
            referer = "kodik.info"
        if not session:
            session = client
            session.headers.update({"referer": referer})
        if not raw_response:
            raw_response = session.get(kodik_player_url).text

        data, new_referer = cls._parse_payload(raw_response, referer)
        api_url = cls._get_api_url(kodik_player_url)
        video_url = cls(session)._get_kodik_video_links(api_url, new_referer, data)["360"][0]["src"]  # type: ignore

        return cls(session)._get_video_quality(video_url, quality)

    def __call__(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Call method for get video url

        :param str player_url: start_kodik url
        :param int quality: video quality. Default 720
        :param str referer: referer headers. default set auto
        :return: direct video url
        """
        # kodik server regular expr detection
        if not self.is_kodik(player_url):
            raise TypeError(
                f"Unknown player balancer. get_video_url method support kodik balancer\nvideo url: {player_url}")
        resp = self._get_raw_payload(player_url, referer)
        # parse payload and url for next request
        data, url_data = self._parse_payload(resp, referer)
        url = self._get_api_url(player_url)

        resp = self.session.post(url, data=data, headers={
            "user-agent": self.useragent,
            "referer": f"https://{url_data}",
            "origin": url.replace("/gvi", ""),
            "accept": "application/json, text/javascript, */*; q=0.01"}).json()["links"]

        # kodik balancer returns max quality 480, but it has (720, 480, 360) values
        video_url = resp["480"][0]["src"]
        return self._get_video_quality(video_url, quality)

    def _get_raw_payload(self, player_url: str, referer: str) -> str:
        return self.session.get(player_url, headers={"user-agent": self.useragent, "referer": referer}).text

    @staticmethod
    def _parse_payload(resp: str, referer: str) -> tuple[dict, str]:
        # sourcery skip: dict-assign-update-to-union
        """parse data for next api request

        url example:
        https://kodik.info/seria/123/hashfoobar123/720p?translations=false&min_age=16

        Example payload signature in html document:
            ...

            var domain = "example.com";

            var d_sign = "hash123foo";

            var pd = "kodik.info";

            var pd_sign = "hash456bar";

            var ref = "https://example.com/";

            var ref_sign = "hash789baz";

            var user_ip = "127.0.0.1";

            var advertScript = null;

            var mediaGenre = "anime";

            var translationId = 610;

            ...


        :param str resp: - html text response
        :param str referer: - referer, where give this url

        :return: - tuple with data and url
        :rtype tuple:
        """
        # prepare values for next POST request
        url_data, = Kodik.RE_URL_DATA.findall(resp)
        type_, = Kodik.RE_VIDEO_TYPE.findall(url_data)
        id_, = Kodik.RE_VIDEO_ID.findall(url_data)
        hash_, = Kodik.RE_VIDEO_HASH.findall(url_data)
        data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", 1)[1].split("&")}
        data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                     "ref": referer.rstrip("/")})
        return data, url_data

    @staticmethod
    def _get_api_url(player_url: str):
        if not player_url.startswith("//"):
            player_url = f"//{player_url}"
        if not player_url.startswith("https:"):
            player_url = f"https:{player_url}"

        url_, = Kodik.RE_URL.findall(player_url)
        return f"https://{urlparse(url_).netloc}/gvi"

    def _get_kodik_video_links(self, api_url: str,
                               new_referer: str,
                               data: dict) -> dict[dict, list[dict]]:
        return self.session.post(api_url, data=data,
                                 headers={"origin": f"https://{new_referer}", "referer": api_url.replace("/gvi", ""),
                                          "accept": "application/json, text/javascript, */*; q=0.01"}).json()["links"]

    def _get_video_quality(self, video_url: str, quality: int) -> str:
        quality = 720 if quality not in self.QUALITY else quality
        video_url = self.decode(video_url).replace("480.mp4", f"{quality}.mp4")
        # issue 8, video_url maybe return 404 code
        if self.session.get(video_url).status_code != 404:
            return video_url

        choose_quality = f"{quality}.mp4"

        for q in self.QUALITY:
            video_url = video_url.replace(choose_quality, f"{q}.mp4")
            if self.session.get(video_url).status_code == 200:
                return video_url
            choose_quality = f"{q}.mp4"
        raise RuntimeError("Video not found", video_url)
