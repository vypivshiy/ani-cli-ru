"""configured session object with ddos protect detector"""
import warnings

from requests import Session, Response

from anicli_ru._defaults import DDOS_SERVICES

__all__ = ('client',)


class SessionM(Session):
    # add custom timeout param https://github.com/psf/requests/issues/3070
    # https://stackoverflow.com/a/62044757
    def __init__(self, timeout=60):
        self.timeout = timeout
        super().__init__()

    def request(self, method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return super().request(method, url, **kwargs)


def check_ddos_protect_hook(resp: Response, **kwargs):
    if resp.headers.get("Server") in DDOS_SERVICES \
            and resp.headers["Connection"] == 'close' \
            and resp.status_code == 403:

        warnings.warn(f"{resp.url} have ddos protect, return 403 code and close this session.",
                      category=RuntimeWarning,
                      stacklevel=2)


client = SessionM()
client.headers.update({"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                     "Chrome/98.0.4758.107 Safari/537.36"})
client.hooks["response"] = [check_ddos_protect_hook]
