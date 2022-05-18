"""Kodik module utils"""
from base64 import b64decode
import re
from urllib.parse import urlparse
try:
    from html.parser import unescape
except ImportError:
    from html import unescape


class Kodik:
    # kodik/anivod regular expressions
    RE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
    RE_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
    RE_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
    RE_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
    RE_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")

    def __init__(self):
        pass

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
        url_data, = re.findall(Kodik.RE_URL_DATA, resp)
        type_, = re.findall(Kodik.RE_VIDEO_TYPE, url_data)
        id_, = re.findall(Kodik.RE_VIDEO_ID, url_data)
        hash_, = re.findall(Kodik.RE_VIDEO_HASH, url_data)
        data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", 1)[1].split("&")}
        data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                     "ref": referer.rstrip("/")})
        return data, url_data

    @staticmethod
    def get_url(raw_player_url: str):
        url_, = Kodik.RE_URL.findall(raw_player_url)
        return f"https://{urlparse(url_).netloc}/gvi"

    @staticmethod
    def is_kodik(url: str) -> bool:
        """return True if url player is kodik"""
        return bool(Kodik.RE_URL.match(url))

    def __bool__(self):
