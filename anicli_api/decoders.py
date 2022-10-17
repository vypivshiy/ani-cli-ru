"""Decoders class for kodik, aniboom"""
# TODO: add asyncio
# TODO create custom error classes
from base64 import b64decode
import re
from html import unescape
from typing import Optional, Dict, List
from urllib.parse import urlparse
import json

from _http import BaseHTTPSync


class Kodik(BaseHTTPSync):
    HEADERS = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36"}
    REFERER = "https://kodik.info"
    RE_ERROR = re.compile(r"<title>Error</title>")
    RE_PATTERNS = (
        re.compile(r'var type = "(?P<type>.*?)";'),
        re.compile(r"videoInfo\.hash = '(?P<hash>\w+)';"),
        re.compile(r'var videoId = "(?P<id>\d+)"'),
    )
    RE_PARAMS = re.compile(r"var urlParams = (?P<params>'{.*?}')")
    RE_VALIDATE_URL = re.compile(r"https://\w+\.\w{2,6}/seria/\d+/\w+/\d{3,4}p")
    BASE_PAYLOAD = {"bad_user": True,
                    "info": "{}"}
    QUALITY = (720, 480, 360)

    def __init__(self):
        super().__init__()
        self.session.headers.update(self.HEADERS)

    @classmethod
    def parse(cls, url: str, *, referer: Optional[str] = None, raw_response: Optional[str] = None):
        url = url.split("?")[0]
        if url != cls():
            raise AttributeError()
        if not referer:
            referer = cls.REFERER
        if not raw_response:
            raw_response = cls().session.get(url, headers={"referer": referer}).text
        if cls.is_banned(raw_response):  # type: ignore
            raise TypeError
        payload = cls._parse_payload(raw_response)  # type: ignore
        api_url = cls._get_api_url(url)
        response = cls()._get_kodik_videos(api_url, referer, payload)
        for k in response.keys():
            response[k][0]['src'] = cls.decode(response[k][0]['src'])
        return response

    def _get_kodik_videos(self, api_url: str, referer: str, payload: dict) -> Dict[Dict, List[Dict]]:
        response = self.session.post(api_url, data=payload,
                                     headers={"origin": f"https://{referer}",
                                              "referer": api_url.replace("/gvi", ""),
                                              "accept": "application/json, text/javascript, */*; q=0.01"})
        return response.json()["links"]

    @classmethod
    def _parse_payload(cls, response: str) -> Dict:
        payload = cls.BASE_PAYLOAD.copy()
        if not (result := cls.RE_PARAMS.search(response)):
            raise TypeError
        result = json.loads(result.groupdict()["params"].strip("'"))
        payload.update(result)  # type: ignore
        for pattern in cls.RE_PATTERNS:
            if result := pattern.search(response):
                payload.update(result.groupdict())
            else:
                raise ValueError(f"fail {pattern.pattern}")
        return payload

    @classmethod
    def is_kodik(cls, url: str) -> bool:
        """return True if url player is kodik."""
        return bool(cls.RE_VALIDATE_URL.match(url))

    @classmethod
    def is_banned(cls, response: str):
        return bool(cls.RE_ERROR.match(response))

    @classmethod
    def _get_api_url(cls, url: str) -> str:
        if not url.startswith("//"):
            url = f"//{url}"
        if not url.startswith("https:"):
            url = f"https:{url}"
        if url_ := cls.RE_VALIDATE_URL.search(url):
            return f"https://{urlparse(url_.group()).netloc}/gvi"
        raise TypeError

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


class Aniboom(BaseHTTPSync):
    RE_M3U8 = re.compile(r'"hls":"{\\"src\\":\\"(?P<m3u8>.*\.m3u8)\\"')
    RE_MPD = re.compile(r'"{\\"src\\":\\"(?P<mpd>.*\.mpd)\\"')
    RE_M3U8_DATA = re.compile(r'#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+),'
                              r'CODECS=".*?",AUDIO=".*?" {4}(?P<src>.*?\.m3u8)')
    REFERER = "https://aniboom.one"
    USERAGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, " \
                "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36 "
    ACCEPT_LANG = "ru-RU"

    def __init__(self):
        super().__init__()
        self.session.headers.update({"user-agent": self.USERAGENT})

    @classmethod
    def parse(cls, url: str, referer: Optional[str] = None) -> Dict:
        if url != cls():
            raise TypeError
        if not referer:
            referer = cls.REFERER
        response = cls()._aniboom_request(url, referer)
        links = cls._extract_links(response)
        links["m3u8"] = cls._parse_m3u8(links["m3u8"], referer)
        return links

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in urlparse(url).netloc

    def __eq__(self, url: str) -> bool:  # type: ignore
        return self.is_aniboom(url)

    def _aniboom_request(self, player_url: str, referer: str) -> str:
        # need set lowercase keys
        r = self.session.get(player_url, headers={"referer": referer})
        return unescape(r.text)

    @classmethod
    def _parse_m3u8(cls, m3u8_url: str, referer: str) -> Dict:
        response = cls().session.get(m3u8_url, headers={"Referer": referer,
                                                        "Accept-Language": cls.ACCEPT_LANG}).text
        result = {}
        for url_data in cls.RE_M3U8_DATA.finditer(response):
            if m3u8_dict := url_data.groupdict():
                result[m3u8_dict["resolution"]] = url_data["src"]
        return result

    @classmethod
    def _extract_links(cls, raw_response: str) -> Dict:
        raw_response = unescape(raw_response)
        result = {}
        if m3u8_url := cls.RE_M3U8.search(raw_response):
            result.update(m3u8_url.groupdict())
        if mpd_url := cls.RE_MPD.search(raw_response):
            result.update(mpd_url.groupdict())
        return result


if __name__ == '__main__':
    Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
