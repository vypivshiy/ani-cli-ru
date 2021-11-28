from base64 import b64decode
from os import system


def kodik_decoder(url_encoded: str) -> str:
    """kodik player video url decoder

    :param str url_encoded: encoded url
    :return: decoded video url"""
    url_encoded = url_encoded[::-1]
    if not url_encoded.endswith("=="):
        url_encoded += "=="
    link = b64decode(url_encoded).decode()
    if not link.startswith("https"):
        link = "https:" + link
    return link


def run_player(url: str, player: str = "mpv", **commands) -> None:
    """

    :param url: hls url
    :param player: local video player. Default mpv
    :param commands: send optional commands.
        key-param="value" convert to: --key-param=value or **{"my-key-param":"c"} = --my-key-param=c
    :return:
    """
    if commands:
        commands = " ".join((f'--{k}="{v}"' for k, v in commands.items()))
        system(f"{player} {url} {commands}")
    else:
        system(f"{player} {url}")


def is_aniboom(url: str):
    """Костыль, который проверяет принадлежность видео к этому балансеру"""
    return "aniboom" in url

