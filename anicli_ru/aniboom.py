from typing import Optional, Tuple
from html import unescape
import warnings

from anicli_ru._http import client
from anicli_ru.defaults import AniboomDefaults, AniboomM3U8Data


class Aniboom:
    def __init__(self):
        self.session = client
        self.headers = self.session.headers.get("user-agent")

    def get_video_url(self, player_url: str, *, quality: int = 1080, referer: str) -> str:
        """

        :param quality:
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
    def _parse_m3u8(m3u8_url: str) -> Tuple[AniboomM3U8Data, ...]:
        m3u8_response = client.get(m3u8_url, headers={
            "Referer": AniboomDefaults.REFERER, "Accept-Language": AniboomDefaults.ACCEPT_LANG}).text

        return tuple(AniboomM3U8Data(qual, url) for qual, url in AniboomDefaults.RE_M3U8_DATA.findall(m3u8_response))

    @classmethod
    def _set_quality(cls, m3u8_url: str, quality: int = 1080) -> str:
        """set video quality. Works only with m3u8 format

        :param m3u8_url: m3u8 url format
        :param quality: video quality. Default 1080
        :return: video url with set quality
        """
        # parse master.m3u8 response
        results = cls._parse_m3u8(m3u8_url)
        return next((
            m3u8_url.replace("master.m3u8", data.url_suffix) for data in results if data.quality.endswith(str(quality))
        ), m3u8_url)

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in url

    def _get_aniboom_html_response(self, player_url: str, referer: str) -> str:
        # need set lowercase keys
        r = self.session.get(player_url, headers={"referer": referer,
                                                  "user-agent": self.session.headers["user-agent"]})
        return unescape(r.text)

    @classmethod
    def _parse_aniboom_response(cls, raw_aniboom_response: str, *, quality: int = 1080, mpd: bool = False) -> str:
        raw_aniboom_response = unescape(raw_aniboom_response)
        if mpd and (url := AniboomDefaults.RE_MPD.findall(raw_aniboom_response)):
            return url[0].replace("\\", "")
        if quality not in AniboomDefaults.QUALITY or quality == 1080:
            return AniboomDefaults.RE_M3U8.findall(raw_aniboom_response)[0].replace("\\", "")
        else:
            return cls._set_quality(AniboomDefaults.RE_M3U8.findall(raw_aniboom_response)[0].replace("\\", ""), quality)

    @classmethod
    def parse(cls, aniboom_player_url: str, *,
              quality: int = 1080,
              mpd: bool = False,
              referer: Optional[str] = None) -> str:

        if not cls.is_aniboom(aniboom_player_url):
            raise TypeError(f"{aniboom_player_url} is not aniboom")
        if not referer:
            referer = AniboomDefaults.REFERER
        resp = cls()._get_aniboom_html_response(aniboom_player_url, referer)
        return cls._parse_aniboom_response(resp, quality=quality, mpd=mpd)

    def __call__(self,
                 aniboom_player_url: str, *,
                 quality: int = 1080,
                 mpd: bool = False,
                 referer: Optional[str] = None) -> str:

        return self.parse(aniboom_player_url, quality=quality, mpd=mpd, referer=referer)
