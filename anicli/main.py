import asyncio
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Dict, List, Optional, cast

import typer
from click import Choice
from rich import get_console
from typer import BadParameter, Option
from typing_extensions import Annotated

import anicli
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
    pretty_exceptions_enable=False,
    pretty_exceptions_short=False,
    pretty_exceptions_show_locals=False,
)

BROWSER_CHOICE = Choice(BROWSER_SUPPORTS)
console = get_console()


def _get_extractors_choice():
    from anicli.common.extractors import get_extractor_modules  # noqa

    return Choice(get_extractor_modules())


@app.command(help="Show app, anicli-api versions and exit")
def version():
    from rich.panel import Panel  # noqa
    from .common.updater import get_api_version  # noqa

    api_version = get_api_version()
    renderable = f"anicli-ru : [bold]{anicli.__version__}[/bold]\nanicli-api: [bold]{api_version}[/bold]"
    panel = Panel(renderable, title="Versions", expand=False)
    console.print(panel)


@app.command(help="update anicli and anicli-api packages")
def update(
    force: Annotated[
        bool, Option("--force", is_flag=True, help="force update api and client")
    ] = False,
):  # noqa: FBT002
    # I do not know a reliable way in which virtual environment the script is running, so
    # we are polling all the listed package managers in a simple way
    from .common.updater import update_tool  # noqa

    update_tool(force=force)


@app.command(help="check updates")
def check_updates():
    from .common.updater import check_for_updates  # noqa
    import asyncio  # noqa
    from .cli.helpers.render import render_update_notification  # noqa

    result = asyncio.run(check_for_updates())
    if result["anicli_api"]["is_outdated"] or result["anicli_ru"]["is_outdated"]:
        render_update_notification(result, console)  # type: ignore
    else:
        console.print("Used actual versions")


def _cb_parse_cache_size(size: str) -> int:
    if size.endswith(("M", "m")) and size[:-1].isdigit():
        return int(size[:-1]) * 1024 * 1024
    elif size.endswith(("K", "k")) and size[:-1].isdigit():
        return int(size[:-1]) * 1024
    elif size.isdigit():  # bytes
        return int(size)
    raise BadParameter("Shoud be integer or have suffix (k, K - kbytes. m, M - mbytes)")


def _cb_parse_ttl(ttl: str) -> int:
    if ttl.endswith(("h", "H")) and ttl[:-1].isdigit():
        return int(ttl[:-1]) * 3600
    elif ttl.endswith(("m", "M")) and ttl[:-1].isdigit():
        return int(ttl[:-1]) * 60
    elif ttl.isdigit():  # seconds
        return int(ttl)
    raise BadParameter(
        "Should be integer or have suffix (m, M - minutes. h, H - hours)"
    )


@app.command(
    help="run local anicli webserver (experimental)",
    epilog="Use in local network only, not adopted to production",
)
def web(
    host: Annotated[str, Option("-h", "--host", help="ip host")] = "127.0.0.1",
    port: Annotated[int, Option("-p", "--port", help="port")] = 8000,
    workers: Annotated[
        int, Option("-mw", "--max-workers", help="uvicorn max workers")
    ] = 1,
    chunk_size: Annotated[
        str,
        Option(
            "-c",
            "--chunk-size",
            help="chunk video stream size. Support suffixes: k/K (kbytes), m/M (mbytes), or plain integer (bytes)",
            callback=_cb_parse_cache_size,
        ),
    ] = "1M",
    source: Annotated[
        str,
        Option(
            "-s",
            "--source",
            click_type=_get_extractors_choice(),
            help="extractor source",
        ),
    ] = "animego",
    # TODO
    ttl: Annotated[
        str,
        Option(
            "--ttl",
            help="cache TTL destroy parsed objects (in seconds). Support suffixes: h/H (hours), m/M (minutes), or plain integer (seconds)",
            callback=_cb_parse_ttl,
        ),
    ] = "12h",  # 12h
):
    """
    Run the web server for watching anime in browser.

    This is an experimental feature for local network use only.
    Not suitable for production deployment.
    """
    try:
        import uvicorn  # noqa

        from .web.server import OPTIONS, app  # noqa
    except ImportError:
        raise BadParameter(
            "web group required fastapi dependency. Add via `anicli-ru[web]`"
        )

    OPTIONS.EXTRACTOR_NAME = source  # type: ignore
    OPTIONS.CHUNK_SIZE = chunk_size  # type: ignore (cast to int by callback)
    OPTIONS.TTL = ttl  # type: ignore (cast to int by callback)
    uvicorn.run(app, host=host, port=port, workers=workers)


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
    except ImportError:
        raise BadParameter("rookiepy dependency required. Add via `anicli-ru[cookies]`")
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


@app.command(help="run cli-repl application (play video via mpv player)")
def cli(
    # fmt: off
    source: Annotated[
        str,
        Option("-s", "--source", click_type=_get_extractors_choice(), help="extractor target"),
    ],
    quality: Annotated[
        int,
        Option("-q", "--quality", help="default video quality"),
    ] = 2060,
    search: Annotated[Optional[str], Option("--search", help="call search by query after start")] = None,
    ongoing: Annotated[bool, Option("--ongoing", help="call ongoing after start")] = False,
    mpv_opts: Annotated[str, Option("-mo", "--mpv-opts", help="extra MPV options/arguments (should be a string)")] = "",
    m3u_size: Annotated[int, Option("--m3u-size", help="max m3u temp playlist")] = 6,
    timeout: Annotated[int, Option("--timeout", help="http client timeout (seconds)")] = 60,
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
            help="extract cookies from browser",
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
        Optional[List[str]],
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
        msg = (
            "Not allowed pass both `--search` and `--ongoing` options. Pick once option"
        )
        raise BadParameter(msg)

    cfg = AnicliContext(
        extractor_name=source,
        quality=quality,
        mpv_opts=mpv_opts,
        m3u_size=m3u_size,
        timeout=timeout,
        proxy=proxy,
        headers=parse_args_headers(header) if header else {},
    )

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
