"""Decoders class for kodik, aniboom"""
# TODO: add asyncio
# TODO create custom error classes
from base64 import b64decode
import re
from html import unescape
from typing import Optional, Dict, List
from urllib.parse import urlparse
import json

from anicli_api._http import BaseHTTPSync


# TODO docstrings, base abc class for direct links extractor, doc errors


class Kodik(BaseHTTPSync):
    HEADERS = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36"}
    REFERER = "https://kodik.info"
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
            raise AttributeError
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
        if not (result := re.search(r"var urlParams = (?P<params>'{.*?}')", response)):
            raise TypeError
        result = json.loads(result.groupdict()["params"].strip("'"))
        payload.update(result)  # type: ignore
        for pattern in (r'var type = "(?P<type>.*?)";',
                        r"videoInfo\.hash = '(?P<hash>\w+)';",
                        r'var videoId = "(?P<id>\d+)"'
                        ):
            if result := re.search(pattern, response):
                payload.update(result.groupdict())
            else:
                raise ValueError
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
    REFERER = "https://animego.org/"
    USERAGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, " \
                "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36"
    ACCEPT_LANG = "ru-RU"

    def __init__(self, *, referer: Optional[str] = None):
        super().__init__()
        if not referer:
            referer = self.REFERER
        self.session.headers.update({"user-agent": self.USERAGENT,
                                     "referer": referer,
                                     "accept-language": self.ACCEPT_LANG,
                                     })
        self.session.headers.pop("x-requested-with")

    @classmethod
    def parse(cls, url: str) -> Dict:
        if url != cls():
            raise TypeError
        cls_ = cls()
        response = cls_._aniboom_request(url)
        links = cls_._extract_links(response)
        if len(links.keys()) == 0:
            raise TypeError("links not found")
        links["m3u8"] = cls_._parse_m3u8(links["m3u8"])
        return links

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in urlparse(url).netloc

    def __eq__(self, url: str) -> bool:  # type: ignore
        return self.is_aniboom(url)

    def _aniboom_request(self, player_url: str) -> str:
        # need set lowercase keys
        r = self.session.get(player_url)
        return unescape(r.text)

    @classmethod
    def _parse_m3u8(cls, m3u8_url: str) -> Dict:
        response = cls().session.get(m3u8_url, headers={"referer": "https://aniboom.one/",
                                                        "origin": "https://aniboom.one",
                                                        "Accept-Language": cls.ACCEPT_LANG}).text
        result = {}
        base_m3u8_url = m3u8_url.replace("/master.m3u8", "")
        for url_data in re.finditer(r'#EXT-X-STREAM-INF:BANDWIDTH=\d+,RESOLUTION=(?P<resolution>\d+x\d+),'
                                    r'CODECS=".*?",AUDIO="\w+"\s(?P<src>\w+\.m3u8)', response):
            if m3u8_dict := url_data.groupdict():
                result[m3u8_dict["resolution"].split("x")[-1]] = f"{base_m3u8_url}{url_data['src']}"
        return result

    @classmethod
    def _extract_links(cls, raw_response: str) -> Dict:
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


if __name__ == '__main__':
    # Kodik.parse("https://kodik.info/seria/1026046/02a256101df196484d68d10d28987fbb/720p")
    print(Aniboom.parse('https://aniboom.one/embed/N9QdKm4Mwz1?episode=1&translation=2'))
