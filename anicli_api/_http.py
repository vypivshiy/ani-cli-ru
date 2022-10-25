from typing import Dict
from html import unescape

from httpx import Client, AsyncClient

TIMEOUT: float = 30.0
HEADERS: Dict[str, str] = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                                         "Mobile Safari/537.36",
                           "x-requested-with": "XMLHttpRequest"}  # required


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance


class BaseHTTPSync:
    """Base sync HTTP with default config session instance"""
    BASE_URL: str
    TIMEOUT: float = TIMEOUT
    HEADERS = HEADERS

    def __init__(self):
        self.session = Client()
        self.session.timeout = self.TIMEOUT
        self.session.headers.update(self.HEADERS)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @staticmethod
    def unescape(text: str) -> str:
        return unescape(text)


class BaseHTTPAsync:
    BASE_URL: str
    TIMEOUT = TIMEOUT
    HEADERS = HEADERS

    def __init__(self):
        self.session = AsyncClient()
        self.session.timeout = self.TIMEOUT
        self.session.headers.update(self.HEADERS)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

    @staticmethod
    def unescape(text: str) -> str:
        return unescape(text)


class BaseSyncExtractorHttp(Singleton, BaseHTTPSync):
    """Base Extractor class"""


class BaseAsyncExtractorHttp(Singleton, BaseHTTPAsync):
    """Base Async Extractor class"""
