"""Kodik module utils"""
from base64 import b64decode
import re
from typing import Optional, Dict
from urllib.parse import urlparse

try:
    from html.parser import unescape
except ImportError:
    from html import unescape

from requests import Session


class Kodik:
    # kodik/anivod regular expressions
    RE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
    RE_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
    RE_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
    RE_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
    RE_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")
    QUALITY = (720, 480, 360)

    def __init__(self, session: Session):
        self.session = session
        self.useragent = self.session.headers.get("user-agent")

    def get_video_url(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        # kodik server regular expr detection
        if not self.is_kodik(player_url):
            raise TypeError(
                f"Unknown player balancer. get_video_url method support kodik balancer\nvideo url: {player_url}")
        resp = self._get_raw_payload(player_url, referer)
        # parse payload and url for next request
        data, url_data = self.parse_payload(resp, referer)
        url = self.get_api_url(player_url)

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

    def _get_videos_json(self, url: str, data: dict, headers: dict) -> dict:
        return self.session.post(url, data=data, headers=headers).json()["links"]

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
    def parse_payload(resp: str, referer: str) -> tuple[dict, str]:
        """Parser from kodik balanser

        :param str resp: - text response html page
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
    def get_api_url(player_url: str):
        if not player_url.startswith("//"):
            player_url = f"//{player_url}"
        if not player_url.startswith("https:"):
            player_url = f"https:{player_url}"

        url_, = Kodik.RE_URL.findall(player_url)
        return f"https://{urlparse(url_).netloc}/gvi"

    @staticmethod
    def is_kodik(url: str) -> bool:
        """return True if url player is kodik"""
        return bool(Kodik.RE_URL.match(url))
