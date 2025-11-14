# TODO: coming soon
import os
import platform
from pathlib import Path
from typing import Any, Dict

import toml

from anicli.common.extractors import get_extractor_modules

# use raw string for initialize comments reason
__DEFAULT_EXTRACTORS = ", ".join(get_extractor_modules())
DEFAULT_CFG = f"""
[cli]
# supports
# {__DEFAULT_EXTRACTORS}
extractor="animego"
# default quality. if source does not exists it, fallback to near value
# eg: 4000 -> 1080 -> 720 -> 480 ...
quality=1080
# extra mpv args or custom profile endpoint
mpv_args=''
# generate template playlist in tempdir (useful for slice-play)
# max m3u playlist size
m3u_size=6
# https/socks5 proxy
# format: schema://user:password@host:port
proxy=''
# format "Key=Value"
# eg:
# headers=["User-Agent=Mozilla 5.0 ...", "Autorization=Bearer secret..."]
headers=[]

# todo coming soon
[web]
host="localhost"
port=10007
"""

APP_NAME = "anicliru"


def get_config_path() -> Path:
    system = platform.system()

    if system == "Windows":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux / Unix
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.toml"


def create_default_config():
    config = get_config_path()
    config.write_text(DEFAULT_CFG, encoding="utf-8")


def read_config() -> Dict[str, Any]:
    config = get_config_path()
    if not config.exists():
        create_default_config()

    text = config.read_text(encoding="utf-8")
    data = toml.loads(text)
    data["config_path"] = config
    return data
