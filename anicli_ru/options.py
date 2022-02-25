import argparse
from os import system
from typing import Optional

from anicli_ru import all_extractors
from anicli_ru.__version__ import __version__
from anicli_ru.utils import Agent

ALL_PARSERS = {k: v for k, v in enumerate(all_extractors())}


def setup_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"anicli-ru {__version__}\n"
                                                 f"See detail info: https://github.com/vypivshiy/ani-cli-ru",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--download",
                        dest="DOWNLOAD",
                        default=False,
                        action="store_true",
                        help="Download mode. Default False. ffmpeg required")
    parser.add_argument("-q", "--quality",
                        dest="QUALITY",
                        type=int,
                        default=720,
                        choices=[360, 480, 720],
                        help="default video quality. Works only kodik. Default 720")
    parser.add_argument("-i", "--instant",
                        dest="INSTANT",
                        default=False,
                        action="store_true",
                        help="Instant view mode. Useful if you want to watch a title without manual switching episodes")
    parser.add_argument("-s", "--source",
                        dest="SOURCE",
                        type=int,
                        default=0,
                        choices=[*range(len(ALL_PARSERS))],
                        help="Site source keys: {}... DEFAULT 0. "
                             "Usage --print-sources for get available parsers".format(
                            ', '.join((str(i) + ' - ' + str(p) for i, p in ALL_PARSERS.items() if i < 3))))
    parser.add_argument("--print-sources",
                        dest="PRINT_SOURCES",
                        default=False,
                        action="store_true",
                        help="Print available source parsers")

    parser.add_argument("-V", "--version",
                        dest="PRINT_VERSION",
                        help="Display version information.",
                        action="version",
                        version=f"anicli-ru {__version__}")

    request_group = parser.add_argument_group("Configure requests", "Options for config request.Session object")
    request_group.add_argument("--disable-agent",
                               dest="RANDOM_AGENT",
                               action="store_true",
                               default=True,
                               help="Disable set random user agent")
    request_group.add_argument("--agent-type",
                               dest="RANDOM_AGENT_TYPE",
                               type=str,
                               choices=["m", "d", "r", "f"],
                               default="m",
                               help="Set randomize agent type. 'm' - mobile, 'd' - desktop, 'r' - random, "f" "
                                    f"- disable randomize. Default 'm'")
    request_group.add_argument("--user-agent",
                               dest="USERAGENT",
                               type=str,
                               default="",
                               help="Set user-agent string")
    request_group.add_argument("--timeout",
                               dest="TIMEOUT",
                               type=float,
                               default=30,
                               help="Request timeout value. Default 30 seconds")
    request_group.add_argument("-p", "--proxy",
                               dest="PROXY",
                               type=str,
                               default="",
                               help="Add proxy for search requests (not for download video). "
                                    "Didn't have auto detect proxy type. Write argument like "
                                    "proxy_type://ip:port@login:pass")
    updater_group = parser.add_argument_group("Update script", "Check and update script from pypi")
    updater_group.add_argument("-U", "--upgrade",
                               dest="UPGRADE",
                               default=False,
                               action="store_true",
                               help="Upgrade script from pypi")
    updater_group.add_argument("-F", "--force",
                               dest="FORCE",
                               default=False,
                               action="store_true",
                               help="Force update script")

    args = parser.parse_args()
    check_args(args)
    return args


def print_sources():
    """print available anime parsers"""
    for k, v in ALL_PARSERS.items():
        print(f"[{k}] {v}")
    exit(0)


def get_agent(key: str) -> Optional[str]:
    if key == "m":
        return Agent.mobile()
    elif key == "d":
        return Agent.desktop()
    elif key == "f":
        return
    return Agent.random()


def get_updates(pypi_package_name: str = "anicli-ru", force: bool = False) -> None:
    """Updater function.
    Download last update for pypi.

    :param str pypi_package_name: pypi package name
    :param bool force: force update. Default False
    """
    import requests
    print("Check updates")
    r = requests.get(f"https://pypi.org/pypi/{pypi_package_name}/json/",
                     headers={"user-agent": f"anicli-ru {__version__} Updater"}).json()
    pypi_version = list(r["releases"].keys())[-1]
    if __version__ != pypi_version:
        print(f"Detect new version (your - {__version__}, pypi - {pypi_version})")
    else:
        print("Used last version")
    if __version__ != pypi_version or force:
        answer = input("Update? (y/n)? ")
        if answer.lower() != "y":
            exit(1)
        print("Start update from pypi")
        system(f"python3 -m pip install {pypi_package_name} -U")
        print("Done.")
    exit(0)


def check_args(args: argparse.Namespace) -> None:
    """check specify optional arguments"""
    if args.UPGRADE:
        get_updates(force=args.FORCE)
    elif args.PRINT_SOURCES:
        print_sources()
