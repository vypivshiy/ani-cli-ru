# TODO: coming soon
import os
import platform
from pathlib import Path

# import toml
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


def _get_base_dir(env_var: str, default_path: Path) -> Path:
    """Resolve base directory and ensure it exists."""
    base = os.getenv(env_var)
    path = Path(base) if base else default_path
    full_path = path / APP_NAME
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path


def get_config_dir() -> Path:
    """Get platform-specific config directory."""
    system = platform.system()
    if system == "Windows":
        return _get_base_dir("APPDATA", Path.home() / "AppData" / "Roaming")
    if system == "Darwin":
        return _get_base_dir("", Path.home() / "Library" / "Application Support")
    return _get_base_dir("XDG_CONFIG_HOME", Path.home() / ".config")


def get_data_dir() -> Path:
    """Get platform-specific data directory."""
    system = platform.system()
    if system == "Windows":
        return get_config_dir()
    if system == "Darwin":
        return _get_base_dir("", Path.home() / "Library" / "Application Support")
    return _get_base_dir("XDG_DATA_HOME", Path.home() / ".local" / "share")


def get_config_path() -> Path:
    """Get config.toml path, create default if missing."""
    config = get_config_dir() / "config.toml"
    if not config.exists():
        config.write_text(DEFAULT_CFG, encoding="utf-8")
    return config


def get_history_path() -> Path:
    """Get history.json path, create empty if missing."""
    history = get_data_dir() / "history.json"
    if not history.exists():
        history.write_text("[]", encoding="utf-8")
    return history


# def read_config() -> Dict[str, Any]:
#     path = get_config_path()
#     text = path.read_text(encoding="utf-8")
#     data = toml.loads(text)
#     data["config_path"] = path
#     return data
