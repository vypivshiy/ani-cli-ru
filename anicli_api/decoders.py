"""Decoders class for kodik, aniboom
Example usage:
    >>> kodik_links = Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
    >>> aniboom_links = Aniboom.parse('https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2')
    >>> print(kodik_links)
    >>> print(aniboom_links)
    >>> # example output:
    >>> # {'360': [{'src': 'https://cloud.kodik-storage.com/...',
    >>> # 'type': 'application/x-mpegURL'}], '480': [{...}], '720': [{...}]}
    >>> # {'m3u8': {'360': 'https://kekistan.cdn-aniboom.com/pq/foobar/media_0.m3u8', '480': ..., '720': ..., '1080': ...},
    >>> # 'mpd': 'https://kekistan.cdn-aniboom.com/pq/PQmM3Dx0XDl/bazfoo.mpd'}
"""
# TODO: add asyncio
# TODO create custom error classes
from abc import ABC, abstractmethod
from base64 import b64decode
import re
from html import unescape
from typing import Dict, Optional
from urllib.parse import urlparse
import json

from anicli_api._http import BaseHTTPSync, BaseHTTPAsync
from anicli_api.exceptions import DecoderError, RegexParseError


class BaseDecoder(ABC):
    ASYNC_HTTP: BaseHTTPAsync = BaseHTTPAsync()
    HTTP: BaseHTTPSync = BaseHTTPSync()

    @classmethod
    @abstractmethod
    def parse(cls, url: str):
        ...

    @classmethod
    @abstractmethod
    async def async_parse(cls, url: str):
        ...

    @abstractmethod
    def __eq__(self, other: str):  # type: ignore
        """compare class instance with url string"""
        ...


class Kodik(BaseDecoder):
    REFERER = "https://kodik.info"
    BASE_PAYLOAD = {"bad_user": True,
                    "info": "{}"}

    @classmethod
    def parse(cls, url: str):
        """High-level kodik video link extractor

        Usage: Kodik.parse(<url>)

        :param str url: kodik url
        :return: dict of direct links
        """
        url = url.split("?")[0]
        if url != cls():
            raise DecoderError(f"{url} is not Kodik")

        raw_response = cls.HTTP.get(url, headers={"referer": cls.REFERER}).text
        if cls.is_banned(raw_response):  # type: ignore
            raise DecoderError("This video is not available in your country")

        payload = cls._parse_payload(raw_response)  # type: ignore
        api_url = cls._get_api_url(url)
        response = cls.HTTP.post(api_url, data=payload,
                                 headers={"origin": cls.REFERER,
                                          "referer": api_url.replace("/gvi", ""),
                                          "accept": "application/json, text/javascript, */*; q=0.01"}).json()["links"]
        response = {quality: cls.decode(response[quality][0]['src']) for quality in response.keys()}  # type: ignore
        if response.get("720") and "480.mp4" in response.get("720"):  # type: ignore
            response["720"] = response.get("720").replace("/480.mp4", "/720.mp4")  # type: ignore
        return response

    @classmethod
    async def async_parse(cls, url: str):
        url = url.split("?")[0]
        if url != cls():
            raise DecoderError(f"{url} is not Kodik")

        async with cls.ASYNC_HTTP as session:
            raw_response = (await session.get(url, headers={"referer": cls.REFERER})).text
            if cls.is_banned(raw_response):  # type: ignore
                raise DecoderError("This video is not available in your country")
            payload = cls._parse_payload(raw_response)  # type: ignore
            api_url = cls._get_api_url(url)
            response = (await session.post(api_url, data=payload,
                                           headers={"origin": cls.REFERER,
                                                    "referer": api_url.replace("/gvi", ""),
                                                    "accept": "application/json, text/javascript, */*; q=0.01"}
                                           )).json()["links"]
            response = {quality: cls.decode(response[quality][0]['src']) for quality in response.keys()}  # type: ignore
            if response.get("720") and "480.mp4" in response.get("720"):  # type: ignore
                response["720"] = response.get("720").replace("/480.mp4", "/720.mp4")  # type: ignore
            return response

    @classmethod
    def _parse_payload(cls, response: str) -> Dict:
        payload = cls.BASE_PAYLOAD.copy()
        if not (result := re.search(r"var urlParams = (?P<params>'{.*?}')", response)):
            raise RegexParseError("Error parse payload params with 'var urlParams = (?P<params>'{.*?}')'")
        result = json.loads(result.groupdict()["params"].strip("'"))
        payload.update(result)  # type: ignore
        for pattern in (r'var type = "(?P<type>.*?)";',
                        r"videoInfo\.hash = '(?P<hash>\w+)';",
                        r'var videoId = "(?P<id>\d+)"'
                        ):
            if result := re.search(pattern, response):
                payload.update(result.groupdict())
            else:
                raise RegexParseError(f"Error parse payload params with '{pattern}'")
        return payload

    @classmethod
    def is_kodik(cls, url: str) -> bool:
        """return True if url player is kodik."""
        return bool(re.match(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p", url))

    @classmethod
    def is_banned(cls, response: str):
        return bool(re.match(r"<title>Error</title>", response))

    @classmethod
    def _get_api_url(cls, url: str) -> str:
        if not url.startswith("//"):
            url = f"//{url}"
        if not url.startswith("https:"):
            url = f"https:{url}"
        if url_ := re.search(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p", url):
            return f"https://{urlparse(url_.group()).netloc}/gvi"
        raise DecoderError(f"{url} is not Kodik")

    def __eq__(self, url: str) -> bool:  # type: ignore
        return self.is_kodik(url) if isinstance(url, str) else NotImplemented

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


class Aniboom(BaseDecoder):
    REFERER = "https://animego.org/"
    ACCEPT_LANG = "ru-RU"

    def __init__(self):
        super().__init__()
        self.HTTP.headers.update({"referer": self.REFERER,
                                  "accept-language": self.ACCEPT_LANG,
                                  })

    @classmethod
    def parse(cls, url: str) -> Dict[str, Optional[str]]:
        """High-level aniboom video link extractor.

        For play video required next headers:

        * user-agent: any desktop/mobile
        * referer: https://aniboom.one/
        * origin: https://aniboom.one
        * accept-language: ru-RU  # increase download speed

        Usage: Aniboom.parse(<url>)

        :param str url: aniboom url
        :return: dict of direct links
        """
        if url != cls():
            raise DecoderError(f"{url} is not Aniboom")
        cls_ = cls()
        response = unescape(cls_.HTTP.get(url).text)

        links = cls_._extract_links(response)
        if len(links.keys()) == 0:
            raise RegexParseError("Failed extract aniboom video links")

        m3u8_response = cls.HTTP.get(links["m3u8"], headers={"referer": cls.REFERER,
                                                             "origin": cls.REFERER.rstrip("/"),
                                                             "accept-language": cls.ACCEPT_LANG}).text
        links["m3u8"] = cls_._parse_m3u8(links["m3u8"], m3u8_response)  # type: ignore # TODO

        return links  # type: ignore  # TODO

    @classmethod
    async def async_parse(cls, url: str) -> Dict[str, str]:
        if url != cls():
            raise DecoderError(f"{url} is not Aniboom")
        cls_ = cls()
        async with cls.ASYNC_HTTP as session:
            response = unescape((await session.get(url)).text)
            links = cls_._extract_links(response)
            if len(links.keys()) == 0:
                raise RegexParseError("Failed extract aniboom video links")
            m3u8_response = (await session.get(links["m3u8"],
                                               headers={"referer": cls.REFERER,
                                                        "origin": cls.REFERER.rstrip("/"),
                                                        "accept-language": cls.ACCEPT_LANG})).text

            links["m3u8"] = cls_._parse_m3u8(links["m3u8"], m3u8_response)  # type: ignore
            return links

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in urlparse(url).netloc

    def __eq__(self, url: str) -> bool:  # type: ignore
        return self.is_aniboom(url)

    @classmethod
    def _parse_m3u8(cls, m3u8_url: str, m3u8_response: str) -> Dict[str, str]:
        result = {}
        base_m3u8_url = m3u8_url.replace("/master.m3u8", "")
        for url_data in re.finditer(r'#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+),'
                                    r'CODECS=".*?",AUDIO="\w+"\s(?P<src>\w+\.m3u8)', m3u8_response):
            if m3u8_dict := url_data.groupdict():
                result[m3u8_dict["resolution"].split("x")[-1]] = f"{base_m3u8_url}/{url_data['src']}"
        return result

    @classmethod
    def _extract_links(cls, raw_response: str) -> Dict[str, str]:
        raw_response = unescape(raw_response)
        result = {}
        if m3u8_url := re.search(r'"hls":"{\\"src\\":\\"(?P<m3u8>.*\.m3u8)\\"', raw_response):
            result.update(m3u8_url.groupdict())
        else:
            result["m3u8"] = None

        if mpd_url := re.search(r'"{\\"src\\":\\"(?P<mpd>.*\.mpd)\\"', raw_response):
            result.update(mpd_url.groupdict())
        else:
            result["mpd"] = None

        for k, v in result.items():
            result[k] = v.replace("\\", "")
        return result
