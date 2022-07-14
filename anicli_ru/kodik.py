"""Kodik module utils"""
import warnings
from base64 import b64decode
from typing import Optional, Pattern, Tuple, Dict, List
from urllib.parse import urlparse


from anicli_ru._http import client
from anicli_ru.defaults import KodikDefaults


class Kodik:
    """Class for parse video from kodik balancer

        Example::
            >>> from anicli_ru.kodik import Kodik
            >>> video = Kodik.parse("https://kodik.info/seria/123/hashfoobar123/720p", referer="kodik.info")

        Or with init this class::
            >>> from anicli_ru.kodik import Kodik
            >>> k = Kodik()
            >>> k.parse("https://kodik.info/seria/123/hashfoobar123/720p")
            >>> # or
            >>> k("https://kodik.info/seria/123/hashfoobar123/720p")
    """
    # kodik/anivod etc regular expressions
    DATA_RE = KodikDefaults.data
    KODIK_URL_VALIDATE = KodikDefaults.KODIK_URL_VALIDATE
    KODIK_REFERER = KodikDefaults.RE_KODIK_REFERER
    QUALITY = KodikDefaults.QUALITY

    def __init__(self):
        self.session = client
        self.useragent = self.session.headers.get("user-agent")

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
        return bool(Kodik.KODIK_URL_VALIDATE.search(url))

    @classmethod
    def parse(cls,
              kodik_player_url: str,
              quality: int = 720,
              *,
              referer: Optional[str] = None,
              raw_response: Optional[str] = None) -> str:
        """
        Class method for get kodik video

        :param kodik_player_url: start kodik player url
        :param quality: video quality. Default None
        :param referer: base source referer. Default None
        :param raw_response: raw response from kodik_player_url object. Default none
        :return: direct video url
        """
        if not cls.is_kodik(kodik_player_url):
            raise TypeError(
                f"Unknown player balancer. get_video_url method support kodik balancer\nvideo url: {kodik_player_url}")
        if not referer:
            referer = f"https://{urlparse(kodik_player_url).netloc}/"
        if not raw_response:
            raw_response = cls()._get_raw_payload(kodik_player_url, referer)

        data, new_referer = cls._parse_payload(raw_response)
        api_url = cls._get_api_url(kodik_player_url)
        video_url = cls()._get_kodik_video_links(api_url, new_referer, data)["360"][0]["src"]  # type: ignore
        return cls()._get_video_quality(video_url, quality)

    def __call__(self, player_url: str, quality: int = 720, *, referer: str = "") -> str:
        """Call method for get video url

        :param str player_url: start_kodik url
        :param int quality: video quality. Default 720
        :param str referer: referer headers. default set auto
        :return: direct video url
        """
        return self.parse(player_url, quality=quality, referer=referer)

    def _get_raw_payload(self, player_url: str, referer: str) -> str:
        return self.session.get(player_url, headers={"user-agent": self.useragent, "referer": referer}).text

    @staticmethod
    def _parse_payload(resp: str) -> Tuple[Dict, str]:
        # sourcery skip: dict-assign-update-to-union

        # prepare values for next POST request
        data = {k: v.findall(resp)[0] if isinstance(v, Pattern) else v for k, v in Kodik.DATA_RE.items()}
        url_data = Kodik.KODIK_REFERER.findall(resp)[0]
        return data, url_data

    @staticmethod
    def _get_api_url(player_url: str):
        if not player_url.startswith("//"):
            player_url = f"//{player_url}"
        if not player_url.startswith("https:"):
            player_url = f"https:{player_url}"

        url_, = Kodik.KODIK_URL_VALIDATE.findall(player_url)
        return f"https://{urlparse(url_).netloc}/gvi"

    def _get_kodik_video_links(self, api_url: str,
                               new_referer: str,
                               data: dict) -> Dict[Dict, List[Dict]]:
        copy_headers = self.session.headers.copy()
        copy_headers.update()

        return self.session.post(api_url, data=data,
                                 headers={"origin": api_url.replace("/gvi", ""), "referer": f"https:{new_referer}",
                                          "accept": "application/json, text/javascript, */*; q=0.01"}).json()["links"]

    def _is_not_404_code(self, url) -> bool:
        return self.session.get(url).status_code != 404

    def _get_video_quality(self, video_url: str, quality: int) -> str:
        quality = 720 if quality not in self.QUALITY else quality
        video_url = self.decode(video_url)
        video_url = video_url.replace("360.mp4", f"{quality}.mp4")
        # issue 8, video_url maybe return 404 code
        if self._is_not_404_code(video_url):
            return video_url

        choose_quality = f"{quality}.mp4"

        for q in self.QUALITY:
            video_url = video_url.replace(choose_quality, f"{q}.mp4")
            if self.session.get(video_url).status_code == 200:
                return video_url
            choose_quality = f"{q}.mp4"
        raise RuntimeError("Video not found", video_url)
