import importlib
from pathlib import Path

import sys
import warnings
from importlib.metadata import version as pkg_version

from anicli.check_updates import check_version
from anicli.cli import APP

__version__ = "5.0.16"

_DEFAULT_SOURCE = "yummy_anime_org"
_DEFAULT_SOURCE_OLD = "animego"

from anicli.cli_utlis import command_available
from anicli.updater import is_installed_in_pipx, is_installed_in_uv, update_pipx, update_uv
from anicli.cookies import BROWSER_SUPPORTS, parse_netscape_cookie_string
from anicli.headers import parse_header_line

def _get_version():
    return f"""anicli-ru {__version__}; anicli-api {pkg_version("anicli-api")}"""


def get_modules(package_name="anicli_api.source"):
    # dynamically get available source extractors
    import importlib.util
    import os

    package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]
    files = os.listdir(package_path)
    return [f[:-3] for f in files if f.endswith(".py") and not f.startswith("__") and not f.endswith("__")]


def run_cli():
    import argparse
    from random import choice

    api_modules = get_modules()
    # avoid exception if anicli-api is not latest
    default_source = _DEFAULT_SOURCE if _DEFAULT_SOURCE in api_modules else _DEFAULT_SOURCE_OLD

    parser = argparse.ArgumentParser(description=_get_version(), usage="anicli-ru [OPTIONS]")
    parser.add_argument(
        "-s",
        "--source",
        default=default_source,
        choices=api_modules,
        help="Anime source provider (Default `yummy_anime_org`)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=2060,
        choices=[0, 144, 240, 360, 480, 720, 1080, 2060],
        help="Set minimal video quality output in /video menu. "
        "If there is no maximum, it will display the closest value. "
        "Eg: if -q 1080 and video not contains 1080 - set 720, 480...0 "
        "(default 1080)",
    )
    parser.add_argument("--search", type=str, default=None, help="run search by query menu")
    parser.add_argument("--ongoing", action="store_true", help="run ongoing menu")
    parser.add_argument(
        "-p",
        "--player",
        type=str,
        default="mpv",
        choices=["mpv", "vlc", "cvlc"],
        help="Set videoplayer target. (default 'mpv')",
    )
    parser.add_argument("-pa", "--player-args", type=str, default="", help="Extra player arguments")
    parser.add_argument(
        "--ffmpeg",
        action="store_true",
        default=False,
        help="DEPRECATED. Usage ffmpeg backend for redirect video buffer to player. "
        "Enable, if your player cannot accept headers params (vlc, for example)",
    )
    parser.add_argument(
        "--m3u",
        action="store_true",
        default=False,
        help="Generate m3u playlist for slice play mode. (default False)",
    )
    parser.add_argument(
        "--m3u-size",
        type=int,
        default=12,
        help="Generate m3u playlist for slice play mode. (default 12)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Make Extractor request via proxy e.g. socks5://127.0.0.1:1080, http://user:passwd@127.0.0.1:443",
    )
    parser.add_argument("--timeout", type=float, default=None, help="Setup request timeout")
    parser.add_argument(
        "-U", "--update",
        action="store_true",
        default=False ,
        help="Update anicli-api package (pipx, uv)")
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        default=False,
        help="Print version and exit")
    parser.add_argument(
        "--cookies",
        type=str,
        default=None,
        help="read cookies file (netscape format) and pass to client")
    parser.add_argument(
        "--cookies-from-browser",
        type=str,
        default=None,
        help="extract cookies from browser and pass to client",
        choices=BROWSER_SUPPORTS)
    parser.add_argument(
        "--header",
        type=str,
        action="append",
        help="Add extra headers to http client, use multiple times (Key=Value)")
    parser.add_argument(
        "--header-file",
        type=str,
        help='Path to file with headers (one per line, Key=Value)')

    namespaces = parser.parse_args()
    if namespaces.version:
        print(_get_version())
        sys.exit(0)

    if namespaces.update:
        _run_updater("anicli-api", "anicli-ru")
        sys.exit(0)

    if namespaces.search and namespaces.ongoing:
        raise argparse.ArgumentTypeError("Should be provide --search or --ongoing flag")

    if APP.CFG.USE_FFMPEG_ROUTE:
        warnings.warn("this key will be deleted in next versions", category=DeprecationWarning)

    if not command_available(f"{APP.CFG.PLAYER} --version"):
        msg = f"'{APP.CFG.PLAYER}' player not found. Install it and check it in $PATH environment variables"
        raise argparse.ArgumentTypeError(msg)

    cookies = {}
    if namespaces.cookies:
        if not Path(namespaces.cookies).is_file():
            msg = f"Cookies file {namespaces.cookies} not found"
            warnings.warn(msg, category=RuntimeWarning)
            cookies = {}
        else:
            Path(namespaces.cookies).read_text(encoding="utf-8")
            cookies = parse_netscape_cookie_string(namespaces.cookies)
            print(f"read {len(cookies)} cookies")
    elif namespaces.cookies_from_browser:
        from anicli.cookies import get_cookies_from_browser
        cookies = get_cookies_from_browser(namespaces.cookies_from_browser)
        print(f"read {len(cookies)} cookies")

    all_headers = {}
    if namespaces.header:
        for line in namespaces.header:
            if '=' not in line:
                raise argparse.ArgumentTypeError(f"Invalid header format: '{line}'. Expected key=value.")
            k, v = parse_header_line(line)
            all_headers[k] = v
    if namespaces.header_file:
        if not Path(namespaces.header_file).is_file():
            msg = f"Headers file {namespaces.header_file} not found"
            warnings.warn(msg, category=RuntimeWarning)
        else:
            lines = Path(namespaces.header_file).read_text(encoding="utf-8")
            for line in lines.splitlines():
                if '=' not in line:
                    raise argparse.ArgumentTypeError(f"Invalid header format: '{line}'. Expected key=value.")
                k, v = parse_header_line(line)
                all_headers[k] = v
    if len(all_headers) > 0:
        print(f"load headers lines {len(all_headers)}")
    # setup eggella app
    module = importlib.import_module(f"anicli_api.source.{namespaces.source}")
    APP.CFG.EXTRACTOR = module.Extractor()
    APP.CFG.USE_FFMPEG_ROUTE = namespaces.ffmpeg
    APP.CFG.PLAYER = namespaces.player
    APP.CFG.MIN_QUALITY = namespaces.quality
    APP.CFG.TIMEOUT = namespaces.timeout
    APP.CFG.PROXY = namespaces.proxy
    APP.CFG.M3U_MAKE = namespaces.m3u
    APP.CFG.M3U_MAX_SIZE = namespaces.m3u_size
    APP.CFG.PLAYER_EXTRA_ARGS = namespaces.player_args
    APP.CFG.COOKIES = cookies
    APP.CFG.HEADERS = all_headers

    if namespaces.search:
        APP.exec_and_loop("search", namespaces.search)
    elif namespaces.ongoing:
        APP.exec_and_loop("ongoing", "")
    else:
        APP.loop()


def _run_updater(*packages: str) -> None:
    for package in packages:
        result, old, new = check_version(package)
        if not new:
            print(f"failed get version from pypi: {package}")
        elif result:
            print("start update")
            if is_installed_in_pipx():
                print("application found: pipx")
                update_pipx()
            elif is_installed_in_uv():
                print("application found: uv")
                update_uv()
            else:
                print("failed detect package manager (uv, pipx). try manually update")
            return
    print("latest version is used")


if __name__ == "__main__":
    run_cli()
