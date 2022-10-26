from typing import Dict
from html import unescape

from httpx import Client, AsyncClient


TIMEOUT: float = 30.0
HEADERS: Dict[str, str] = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                                         "Mobile Safari/537.36",
                           "x-requested-with": "XMLHttpRequest"}  # required

__all__ = (
    "BaseHTTPSync",
    "BaseHTTPAsync",
    "HTTPSync",
    "HTTPAsync"
)


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance


class BaseHTTPSync(Client):
    _DEFAULT_HEADERS = HEADERS
    _DEFAULT_TIMEOUT: float = TIMEOUT

    def __init__(self):
        super().__init__()
        self.headers.update(self._DEFAULT_HEADERS)
        self.timeout = self._DEFAULT_TIMEOUT
        self.follow_redirects = True

    @staticmethod
    def unescape(text: str) -> str:
        return unescape(text)


class BaseHTTPAsync(AsyncClient):
    _DEFAULT_HEADERS = HEADERS
    _DEFAULT_TIMEOUT: float = TIMEOUT

    def __init__(self):
        super().__init__()
        self.headers.update(self._DEFAULT_HEADERS)
        self.timeout = self._DEFAULT_TIMEOUT

    @staticmethod
    def unescape(text: str) -> str:
        return unescape(text)


class HTTPSync(Singleton, BaseHTTPSync):
    """Base singleton sync HTTP with recommended config"""


class HTTPAsync(Singleton, BaseHTTPAsync):
    """Base singleton async HTTP class with recommended config"""
