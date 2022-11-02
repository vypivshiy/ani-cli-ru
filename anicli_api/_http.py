import warnings
from typing import Dict
from html import unescape

from httpx import Client, AsyncClient, Response


TIMEOUT: float = 30.0
HEADERS: Dict[str, str] = {"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                                         "Mobile Safari/537.36",
                           "x-requested-with": "XMLHttpRequest"}  # required
DDOS_SERVICES = ("cloudflare", "ddos-guard")  # check ddos-protect strings response

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
        self.follow_redirects = True

    @staticmethod
    def unescape(text: str) -> str:
        return unescape(text)


# simple check ddos protect hook
def check_ddos_protect_hook(resp: Response):
    if resp.headers.get("Server") in DDOS_SERVICES \
            and resp.headers["Connection"] == 'close' \
            or resp.status_code == 403:
        raise ConnectionError(f"{resp.url} have ddos protect {resp.headers.get('Server')} and return 403 code.")


class HTTPSync(Singleton, BaseHTTPSync):
    """Base singleton sync HTTP with recommended config"""

    def __init__(self):
        super(HTTPSync, self).__init__()
        self.event_hooks.update({"response": [check_ddos_protect_hook]})


class HTTPAsync(Singleton, BaseHTTPAsync):
    """Base singleton async HTTP class with recommended config"""

    def __init__(self):
        super(HTTPAsync, self).__init__()
        self.event_hooks.update({"response": [check_ddos_protect_hook]})
