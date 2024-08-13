import re
import subprocess
from importlib.metadata import version as py_module_version


def _mpv_version():
    proc = subprocess.Popen('mpv --version', shell=True, stdout=subprocess.PIPE, text=True)
    stdout = proc.stdout.readline()
    if m := re.search('mpv (.*?) Copyright', stdout):
        return m[1]
    return "mpv path not founded"


def _anicli_api_version():
    return py_module_version("anicli-api")


def _app_version():
    from anicli.version import __VERSION__
    return __VERSION__


LOGO_HEADER = r"""
⠆⠠⡆⠘⠄⠑⠛⠀⠈⠃⢰⡤              _      _ _                  
⠔⣄⡇⠇⠀⠀⠀⠀⠀⠀⢾    __ _ _ __ (_) ___| (_)      _ __ _   _ ⠀
⢠⠋⣶⠀⣤⠀⠀⠀⢰⢰⣾   / _` | '_ \| |/ __| | |_____| '__| | | |  Client Ver.: {} 
⢈⡆⣿⠄⣀⣀⢀⣀⡠⠜⢸  | (_| | | | | | (__| | |_____| |  | |_| |  API ver.   : {} 
⠘⠀⣿⣠⣶⣏⣽⣶⣄⠀⠇   \__,_|_| |_|_|\___|_|_|     |_|   \__,_|  mpv ver.   : {}
[@click=app.open_page("https://github.com/vypivshiy/ani-cli-ru")]🌐 Source[/]
""".strip().format(_app_version(), _anicli_api_version(), _mpv_version())
