import asyncio
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, cast

import typer
from click import Choice
from rich import get_console
from typer import BadParameter, Option
from typing_extensions import Annotated

from anicli.common.extractors import (
    get_extractor_modules,
)
from anicli.common.cookies_config import (
    BROWSER_SUPPORTS,
    parse_args_headers,
    parse_headers_file,
    read_from_browser,
    read_from_netscape_file,
)

from .cli.contexts import AnicliContext
from .common.mpv import is_mpv_installed
from .common.utils import validate_proxy_url

app = typer.Typer(
    # no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_short=False,
    pretty_exceptions_show_locals=False,
)
EXTRACTORS_CHOICE = Choice(get_extractor_modules())
BROWSER_CHOICE = Choice(BROWSER_SUPPORTS)
console = get_console()
APP_VERSION = "6.0.0a"


@app.command(help="show app and api versions and exit")
def version():
    from rich.panel import Panel  # noqa
    from importlib.metadata import version as pkg_version  # noqa

    api_version = pkg_version("anicli-api")
    renderable = f"anicli-ru : [bold]{APP_VERSION}[/bold]\nanicli-api: [bold]{api_version}[/bold]"
    panel = Panel(renderable, title="Versions", expand=False)
    console.print(panel)


@app.command(help="update anicli and anicli-api and exit")
def update(force: Annotated[bool, Option("--force", is_flag=True, help="force update client")] = False):  # noqa: FBT002
    # I do not know a reliable way in which virtual environment the script is running, so
    # we are polling all the listed package managers in a simple way
    from .common.updater import update_pipx, update_uv, is_installed_in_pipx, is_installed_in_uv  # noqa

    is_pipx, is_uv = is_installed_in_pipx(), is_installed_in_uv()
    if not is_pipx and not is_uv:
        msg = "anicli-ru package not founded in pipx or uv tool"
        raise BadParameter(msg)
    if is_uv:
        update_uv(force=force)
    elif is_pipx:
        update_pipx(force=force)


# typer callbacks
def _cb_check_proxy_opt(proxy: Optional[str]) -> Optional[str]:
    # not passed argument, skip
    if not proxy:
        return proxy

    try:
        validate_proxy_url(proxy)
    except ValueError:
        msg = "Invalid proxy URL"
        raise BadParameter(msg)
    return proxy


def _cb_check_read_browser_cookie_opt(browser_name: str) -> Optional[CookieJar]:
    if not browser_name:
        return None
    try:
        cookies = read_from_browser(browser_name)
        return cookies
    except Exception as e:
        raise BadParameter(e.args[0])


def _cb_check_read_netscape_cookies_opt(netscape_cookies: Path) -> Optional[CookieJar]:
    if not netscape_cookies:
        return None
    try:
        cookies = read_from_netscape_file(netscape_cookies)
        return cookies
    except Exception as e:
        raise BadParameter(e.args[0]) from e


def _cb_parse_headers_file(headers_file: Path) -> Optional[Dict[str, str]]:
    if not headers_file:
        return None
    try:
        headers = parse_headers_file(headers_file)
        return headers
    except Exception as e:
        raise BadParameter(e.args[0]) from e


# end typer callbacks


@app.command(help="run cli-repl application")
def cli(
    # fmt: off
    source: Annotated[
        str,
        Option("-s", "--source", click_type=EXTRACTORS_CHOICE, help="extractor target"),
    ],
    quality: Annotated[
        int,
        Option("-q", "--quality", help="default video quality"),
    ] = 2060,
    search: Annotated[Optional[str], Option("--search", help="call search after start")] = None,
    ongoing: Annotated[bool, Option("--ongoing", help="call ongoing after start")] = False,
    mpv_opts: Annotated[str, Option("-mo", "--mpv-opts", help="Extra MPV options/arguments (should be a string)")] = "",
    m3u_size: Annotated[int, Option("--m3u-size", help="max m3u temp playlist")] = 6,
    timeout: Annotated[int, Option("--timeout", help="http client timeout")] = 60,
    proxy: Annotated[
        Optional[str],
        Option(
            "--proxy",
            help="Proxy for anicli-api client, like scheme://user:password@host:port",
            callback=_cb_check_proxy_opt,
        ),
    ] = None,
    extract_cookies_from_browser: Annotated[
        Optional[str],
        Option(
            "--cookies-from-browser",
            help="extract cookies from browser (rookiepy required)",
            click_type=BROWSER_CHOICE,
            # !!! cast to CookieJar type if arg passed else None
            callback=_cb_check_read_browser_cookie_opt,
        ),
    ] = None,
    netscape_cookies: Annotated[
        Optional[Path],
        Option(
            "--cookies",
            help="read cookies from file in netscape format",
            # !!! cast to CookieJar type if arg passed else None
            callback=_cb_check_read_netscape_cookies_opt,
        ),
    ] = None,
    header: Annotated[
        List[str],
        Option(
            "-H",
            "--header",
            help="Add extra headers to HTTP client, can be used multiple times (Key=Value)",
        ),
    ] = None,
    headers_file: Annotated[
        Optional[Path],
        Option(
            "--header-file",
            help="Path to file with headers (one per line, Key=Value)",
            # !!! cast to Dict[str,str] type if arg passed else None
            callback=_cb_parse_headers_file,
        ),
    ] = None,
) -> None:
    # fmt: on
    if not is_mpv_installed():
        msg = (
            "MPV player is not installed or cannot be found in your system PATH.\n"
            "The command 'mpv' must be runnable from your terminal/command prompt.\n"
            "Please install MPV from: https://mpv.io/\n"
        )
        raise BadParameter(msg)
    if search and ongoing:
        msg = "Not allowed pass both `--search` and `--ongoing` options. Pick once option"
        raise BadParameter(msg)

    cfg = AnicliContext()

    cfg["extractor_name"] = source
    cfg["quality"] = quality if quality else 2060
    cfg["mpv_opts"] = mpv_opts if mpv_opts else ""
    cfg["m3u_size"] = m3u_size if m3u_size else 6
    cfg["timeout"] = timeout if timeout else 60
    cfg["proxy"] = proxy if proxy else None

    if extract_cookies_from_browser:
        extract_cookies_from_browser = cast(CookieJar, extract_cookies_from_browser)
        cfg["cookies"] = extract_cookies_from_browser

    if netscape_cookies:
        netscape_cookies = cast(CookieJar, netscape_cookies)
        if cfg.get("cookies", None):
            cfg["cookies"] = netscape_cookies
        else:
            for cookie in netscape_cookies:
                cfg["cookies"].set_cookie(cookie)

    cfg["headers"] = parse_args_headers(header) if header else {}
    if headers_file:
        headers_file = cast(Dict[str, str], headers_file)
        cfg["headers"].update(headers_file)

    # push settings and run
    from .cli.main import APP

    # Update the app_context within the AppContext container, not replace the entire container
    APP.context._data.update(cfg)
    if search:
        cmd_key, raw_args = "search", search
    elif ongoing:
        cmd_key, raw_args = "ongoing", ""
    else:
        cmd_key, raw_args = None, None
    asyncio.run(APP.run(cmd_key=cmd_key, raw_args=raw_args))


def main():
    app()


if __name__ == "__main__":
    main()
