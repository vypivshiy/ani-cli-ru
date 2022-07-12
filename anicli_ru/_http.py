"""configured session object with ddos protect detector"""
import warnings

from requests import Session, Response

from anicli_ru.defaults import DDOS_SERVICES, BASE_HEADERS_DICT

__all__ = ('client', 'SessionM')


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
            or resp.status_code == 403:

        warnings.warn(f"{resp.url} have ddos protect and return 403 code.",
                      category=RuntimeWarning,
                      stacklevel=2)


client = SessionM()
client.headers.update(BASE_HEADERS_DICT)
client.hooks["response"] = [check_ddos_protect_hook]
