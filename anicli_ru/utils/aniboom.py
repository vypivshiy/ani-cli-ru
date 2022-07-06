import warnings
import re
from typing import NamedTuple, Optional

try:
    from html.parser import unescape
except ImportError:
    from html import unescape

from requests import Session

from anicli_ru._http import client


class AniboomM3U8Data(NamedTuple):
    quality: str
    url_suffix: str


class Aniboom:
    # aniboom regular expressions (works after unescape method response html page)
    RE_M3U8 = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
    RE_MPD = re.compile(r'"{\\"src\\":\\"(.*\.mpd)\\"')
    QUALITY = (1080, 720, 480, 360)  # works only m3u8 format
    RE_M3U8_DATA = re.compile(r'''#EXT\-X\-STREAM\-INF\:BANDWIDTH=\d+,RESOLUTION=(\d+x\d+),CODECS=".*?",AUDIO=".*?"
(.*?\.m3u8)''')  # parse master.m3u8, return [(quality, url), ...] results

    def __init__(self, session: Optional[Session] = None):
        self.session = session or client
        self.headers = self.session.headers.get("user-agent")

    def get_video_url(self, player_url: str, *, quality: int = 1080, referer: str) -> str:
        """

        :param player_url:
        :param referer:
        :return:
        """
        warnings.warn("Usage Aniboom.parse() or Aniboom()() methods", category=DeprecationWarning, stacklevel=2)
        return self.parse(player_url, quality=quality, referer=referer)

    @staticmethod
    def get_aniboom_url(raw_aniboom_response: str, *, quality: int = 1080, mpd: bool = False) -> str:
        """
        :param quality: video quality. Available values: 480, 720, 1080
        :param raw_aniboom_response:
        :param mpd: return mpd url extension. Default False
        :return: video url
        """
        warnings.warn("Usage Aniboom.parse() or Aniboom()() methods", category=DeprecationWarning, stacklevel=2)

        return Aniboom._parse_aniboom_response(raw_aniboom_response, quality=quality, mpd=mpd)

    @staticmethod
    def _set_quality(m3u8_url: str, quality: int = 1080) -> str:
        """set video quality. Works only with m3u8 format

        :param m3u8_url: m3u8 url format
        :param quality: video quality. Default 1080
        :return: video url with set quality
        """
        # parse master.m3u8 response
        r = client.get(m3u8_url, headers={"Referer": "https://aniboom.one", "Accept-Language": "ru-RU",
                                          "User-Agent":
                                              "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                                              "Chrome/94.0.4606.114 Mobile Safari/537.36"}).text

        # '640x360' - 360 '854x480' 480 '1280x720' - 720 '1920x1080' - 1080
        results = [AniboomM3U8Data(qual, url) for qual, url in Aniboom.RE_M3U8_DATA.findall(r)]
        return next((
            m3u8_url.replace("master.m3u8", data.url_suffix) for data in results if data.quality.endswith(str(quality))
        ), m3u8_url)

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in url

    def _get_aniboom_html_response(self, player_url: str, referer: str) -> str:
        # need set lowercase

        r = self.session.get(player_url, headers={"referer": referer,
                                                  "user-agent": self.session.headers["user-agent"]})

        return unescape(r.text)

    @classmethod
    def _parse_aniboom_response(cls, raw_aniboom_response: str, *, quality: int = 1080, mpd: bool = False) -> str:
        raw_aniboom_response = unescape(raw_aniboom_response)

        if mpd and len(cls.RE_MPD.findall(raw_aniboom_response)) != 0:
            return cls.RE_MPD.findall(raw_aniboom_response)[0].replace("\\", "")

        if quality not in cls.QUALITY or quality == 1080:
            return cls.RE_M3U8.findall(raw_aniboom_response)[0].replace("\\", "")
        else:
            return cls._set_quality(cls.RE_M3U8.findall(raw_aniboom_response)[0].replace("\\", ""), quality)

    @classmethod
    def parse(cls, aniboom_player_url: str, *,
              quality: int = 1080,
              mpd: bool = False,
              referer: Optional[str] = None,
              session: Optional[Session] = None) -> str:
        if not cls.is_aniboom(aniboom_player_url):
            raise TypeError(f"{aniboom_player_url} is not aniboom")

        if not session:
            session = client
        if not referer:
            referer = "aniboom.one"
        resp = cls(session)._get_aniboom_html_response(aniboom_player_url, referer)
        return cls._parse_aniboom_response(resp, quality=quality, mpd=mpd)

    def __call__(self,
                 aniboom_player_url: str, *,
                 quality: int = 1080,
                 mpd: bool = False,
                 referer: Optional[str] = None,
                 session: Optional[Session] = None):
        return self.parse(aniboom_player_url, quality=quality, mpd=mpd, referer=referer, session=session)
