"""
This module contains functions for works video hosting


UPD: DEPRECATED
"""


from base64 import b64decode
import re
from urllib.parse import urlparse
try:
    from html.parser import unescape
except ImportError:
    from html import unescape

import warnings

# aniboom regular expressions (works after unescape method response html page)
RE_ANIBOOM = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
RE_ANIBOOM_MPD = re.compile(r'"{\\"src\\":\\"(.*\.mpd)\\"')

# kodik/anivod regular expressions
RE_KODIK_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
RE_KODIK_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
RE_KODIK_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
RE_KODIK_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
RE_KODIK_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")


def kodik_decoder(url_encoded: str) -> str:
    """kodik player video url decoder

    :param str url_encoded: encoded url
    :return: decoded video url"""
    warnings.warn("Function kodik_decoder is deprecated; The function "
                  "kodik_decoder is deprecated and will be removed later."
                  "use utils.Kodik.decode method",
                  category=DeprecationWarning)
    url_encoded = url_encoded[::-1]
    if not url_encoded.endswith("=="):
        url_encoded += "=="
    link: str = b64decode(url_encoded).decode()
    if not link.startswith("https"):
        link = f"https:{link}"
    return link


def kodik_parse_payload(resp: str, referer: str) -> tuple[dict, str]:
    """Parser from kodik balanser

    :param str resp: - text response html page
    :param str referer: - referer, where give this url

    :return: - tuple with data and url
    :rtype tuple:
    """
    # prepare values for next POST request
    warnings.warn("Function kodik_parse_payload is deprecated; The function "
                  "kodik_parse_payload is deprecated and will be removed later."
                  "use utils.Kodik.parse_payload method",
                  category=DeprecationWarning)
    url_data, = re.findall(RE_KODIK_URL_DATA, resp)
    type_, = re.findall(RE_KODIK_VIDEO_TYPE, url_data)
    id_, = re.findall(RE_KODIK_VIDEO_ID, url_data)
    hash_, = re.findall(RE_KODIK_VIDEO_HASH, url_data)
    data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", 1)[1].split("&")}
    data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                 "ref": referer.rstrip("/")})
    return data, url_data


def get_kodik_url(raw_player_url: str):
    warnings.warn("Function get_kodik_url is deprecated; The function "
                  "get_kodik_url is deprecated and will be removed later."
                  "use utils.Kodik.parse_payload method",
                  category=DeprecationWarning)
    url_, = RE_KODIK_URL.findall(raw_player_url)
    return f"https://{urlparse(url_).netloc}/gvi"


def get_aniboom_url(raw_aniboom_response: str, *, mpd=True):
    warnings.warn("Function get_aniboom_url is deprecated; The function "
                  "get_aniboom_url is deprecated and will be removed later."
                  "use utils.Aniboom.get_url method",
                  category=DeprecationWarning)
    r = unescape(raw_aniboom_response)
    if mpd:
        return RE_ANIBOOM_MPD.findall(r)[0].replace("\\", "")
    return RE_ANIBOOM.findall(r)[0].replace("\\", "")


def is_kodik(url: str):
    """return True if player url is kodik"""
    warnings.warn("Function is_kodik is deprecated; The function "
                  "is_kodik is deprecated and will be removed later."
                  "use utils.Kodik.is_kodik method",
                  category=DeprecationWarning)
    return bool(RE_KODIK_URL.match(url))


def is_aniboom(url: str) -> bool:
    """return True if player url is aniboom"""
    warnings.warn("Function is_aniboom is deprecated; The function "
                  "is_aniboom is deprecated and will be removed later."
                  "use utils.Aniboom.is_aniboom method",
                  category=DeprecationWarning)
    return "aniboom" in url
