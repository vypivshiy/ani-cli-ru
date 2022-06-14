from base64 import b64decode
import re
from urllib.parse import urlparse
from typing import NamedTuple

try:
    from html.parser import unescape
except ImportError:
    from html import unescape

from requests import Session


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

    def __init__(self, session: Session):
        self.session = session
        self.headers = self.session.headers.get("user-agent")

    def get_video_url(self, player_url: str, *, quality: int = 1080, mpd: bool = False, referer: str) -> str:
        """

        :param player_url:
        :param quality:
        :param mpd:
        :param referer:
        :return:
        """
        r = self.session.get(player_url, headers={"referer": referer,
                                                  "user-agent": self.session.headers["user-agent"]})

        return self.get_aniboom_url(r.text, quality=quality, mpd=mpd)

    @staticmethod
    def get_aniboom_url(raw_aniboom_response: str, *, quality: int = 1080, mpd: bool = False) -> str:
        """

        :param quality: video quality. Available values: 480, 720, 1080
        :param raw_aniboom_response:
        :param mpd: return mpd url extension. Default False
        :return: video url
        """
        r = unescape(raw_aniboom_response)
        try:
            if mpd:
                return Aniboom.RE_MPD.findall(r)[0].replace("\\", "")
        except IndexError:
            if quality not in Aniboom.QUALITY or quality == 1080:
                return Aniboom.RE_M3U8.findall(r)[0].replace("\\", "")
            else:
                return Aniboom._set_quality(Aniboom.RE_M3U8.findall(r)[0].replace("\\", ""), quality)

    @staticmethod
    def _set_quality(m3u8_url: str, quality: int = 1080) -> str:
        """set video quality. Works only with m3u8 format

        :param m3u8_url: m3u8 url format
        :param quality: video quality. Default 1080
        :return: video url with set quality
        """
        # parse master.m3u8 response
        r = Session().get(m3u8_url, headers={"Referer": "https://aniboom.one", "Accept-Language": "ru-RU",
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
