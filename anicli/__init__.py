import importlib

import pkg_resources

from anicli.cli import APP

__version__ = "5.0.10"


def _get_version():
    return f"""anicli-ru {__version__}; anicli-api {pkg_resources.get_distribution("anicli-api").version}"""


def get_modules(package_name='anicli_api.source'):
    # dynamically get available source extractors
    import os
    import importlib.util
    package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]
    files = os.listdir(package_path)
    return [f[:-3] for f in files if f.endswith('.py') and not f.startswith('__') and not f.endswith('__')]


def run_cli():
    import argparse

    parser = argparse.ArgumentParser(description=_get_version(), usage="anicli-ru [OPTIONS]")
    parser.add_argument(
        "-s",
        "--source",
        default="animego",
        choices=get_modules(),
        help="Anime source provider (Default `animego`)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=1080,
        choices=[0, 144, 240, 360, 480, 720, 1080],
        help="Set minimal video quality output in /video menu. "
        "If there is no maximum, it will display the closest value. "
        "Eg: if -q 1080 and video not contains 1080 - set 720, 480...0 "
        "(default 1080)",
    )
    parser.add_argument(
        "-p",
        "--player",
        type=str,
        default="mpv",
        choices=["mpv", "vlc", "cvlc"],
        help="Set videoplayer target. (default 'mpv')",
    )
    parser.add_argument(
        "--ffmpeg",
        action="store_true",
        default=False,
        help="Usage ffmpeg backend for redirect video buffer to player. "
        "Enable, if your player cannot accept headers params (vlc, for example)",
    )
    parser.add_argument(
        "--m3u",
        action="store_true",
        default=False,
        help="Generate m3u playlist for slice play mode. "
             "(default False)",
    )
    parser.add_argument(
        "--m3u-size",
        type=int,
        default=12,
        help="Generate m3u playlist for slice play mode. "
             "(default 12)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Make Extractor request via proxy e.g. socks5://127.0.0.1:1080, http://user:passwd@127.0.0.1:443",
    )
    parser.add_argument("--timeout", type=float, default=None, help="Setup request timeout")
    parser.add_argument("-v", "--version", action="store_true", default=False, help="Print version and exit")

    namespaces = parser.parse_args()
    if namespaces.version:
        print(_get_version())
        exit(0)
    # setup eggella app
    module = importlib.import_module(f"anicli_api.source.{namespaces.source}")
    APP.CFG.EXTRACTOR = getattr(module, "Extractor")()
    APP.CFG.USE_FFMPEG_ROUTE = namespaces.ffmpeg
    APP.CFG.PLAYER = namespaces.player
    APP.CFG.MIN_QUALITY = namespaces.quality
    APP.CFG.TIMEOUT = namespaces.timeout
    APP.CFG.PROXY = namespaces.proxy
    APP.CFG.M3U_MAKE = namespaces.m3u
    APP.CFG.M3U_MAX_SIZE = namespaces.m3u_size
    APP.loop()


if __name__ == '__main__':
    run_cli()
