import warnings
from typing import Dict, Any

import sys
from httpx import Cookies

if sys.platform == "darwin":
    BROWSER_SUPPORTS = [
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
        "safari",
    ]
elif sys.platform == "win32":
    BROWSER_SUPPORTS = [
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
        # lib support it, why not?
        "internet_explorer",
        "octo_browser",
    ]
else:
    BROWSER_SUPPORTS = [
        "firefox",
        "librewolf",
        "brave",
        "edge",
        "chrome",
        "chromium",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "chromium_based",
        "firefox_based",
        "any_browser",
    ]


def get_cookies_from_browser(browser_name: str = "any_browser") -> Cookies:
    try:
        from anicli_api.tools.cookies import get_raw_cookies_from_browser, \
            raw_cookies_to_httpx_cookiejar  # type: ignore
    except ImportError:
        warnings.warn("extract cookies from browser required `anicli-ru[browser-cookies]` dependency.",
                      category=ImportWarning)
        exit(1)
    cookies = get_raw_cookies_from_browser(browser_name)  # type: ignore
    return raw_cookies_to_httpx_cookiejar(cookies)


# duplicate logic from anicli-api.tools.cookies
# read netscape format not require rookiepy dependency
def parse_netscape_cookie_line(netscape_cookie_line: str) -> Dict[str, Any]:
    line = netscape_cookie_line.strip()
    if not netscape_cookie_line or line.startswith("#"):
        return {}
    parts = line.split("\t")
    if len(parts) != 7:
        return {}
    domain, domain_flag, path, secure, expires, name, value = parts
    return {
        "domain": domain,
        "flag": domain_flag == "TRUE",  # Convert to boolean
        "path": path,
        "secure": secure == "TRUE",  # Convert to boolean
        "expires": int(expires),  # Convert to timestamp
        "name": name,
        "value": value,
    }


def parse_netscape_cookie_string(netscape_cookie_string: str) -> Cookies:
    httpx_cookie = Cookies()
    for line in netscape_cookie_string.splitlines():
        cookie = parse_netscape_cookie_line(line)
        if not cookie:
            continue
        httpx_cookie.set(name=cookie["name"], value=cookie["value"], domain=cookie["domain"], path=cookie["path"])
    return httpx_cookie
