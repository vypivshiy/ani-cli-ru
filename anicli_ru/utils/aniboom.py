from base64 import b64decode
import re
from urllib.parse import urlparse

try:
    from html.parser import unescape
except ImportError:
    from html import unescape


from requests import Session


class Aniboom:
    # aniboom regular expressions (works after unescape method response html page)
    RE_M3U8 = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
    RE_MPD = re.compile(r'"{\\"src\\":\\"(.*\.mpd)\\"')

    def __init__(self, session: Session):
        self.session = session
        self.headers = self.session.headers.get("user-agent")

    def get_video_url(self, player_url: str, *, referer: str) -> str:
        r = self.session.get(player_url, headers={"referer": referer,
                                                  "user-agent": self.session.headers["user-agent"]})

        return self.get_aniboom_url(r.text)

    @staticmethod
    def get_aniboom_url(raw_aniboom_response: str, *, mpd=True) -> str:
        """
        """
        r = unescape(raw_aniboom_response)
        try:
            if mpd:
                return Aniboom.RE_MPD.findall(r)[0].replace("\\", "")
        finally:
            return Aniboom.RE_M3U8.findall(r)[0].replace("\\", "")

    @staticmethod
    def is_aniboom(url: str) -> bool:
        """return True if player url is aniboom"""
        return "aniboom" in url
