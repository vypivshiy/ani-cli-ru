# TODO: coming soon
import json
import os
import platform
from pathlib import Path
from typing import Dict, List

import attr

# import toml
from anicli.common.extractors import (
    dynamic_load_extractor_module,
    get_extractor_modules,
)

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


class AppManager:
    APP_NAME = "anicliru"

    @classmethod
    def get_config_dir(cls) -> Path:
        system = platform.system()
        if system == "Windows":
            base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = base / cls.APP_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_data_dir(cls) -> Path:
        system = platform.system()
        if system == "Windows":
            return cls.get_config_dir()
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        path = base / cls.APP_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_config_path(cls) -> Path:
        config = cls.get_config_dir() / "config.toml"
        if not config.exists():
            config.write_text(DEFAULT_CFG, encoding="utf-8")
        return config

    @classmethod
    def get_history_path(cls) -> Path:
        history = cls.get_data_dir() / "history.json"
        if not history.exists():
            history.write_text("[]", encoding="utf-8")
        return history

    @classmethod
    def read_history(cls) -> List[Dict]:
        path = cls.get_history_path()
        try:
            with path.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    @classmethod
    def save_history(cls, item, extractor_name: str):
        full_data = attr.asdict(item)

        clean_data = {k: v for k, v in full_data.items() if not k.startswith("_")}

        entry_data = {
            "title": clean_data.pop("title", "Unknown"),
            "thumbnail": clean_data.pop("thumbnail", ""),
            "url": clean_data.pop("url", ""),
            "data": clean_data,
        }

        entry = {
            "extractor_name": extractor_name,
            "type": item.__class__.__name__,
            "data": entry_data,
        }

        history = cls.read_history()

        history = [e for e in history if e["data"]["url"] != entry_data["url"]]
        history.insert(0, entry)

        with cls.get_history_path().open("w", encoding="utf-8") as f:
            json.dump(history[:50], f, ensure_ascii=False, indent=4)

    @classmethod
    def load_history(cls):
        raw_data = cls.read_history()
        results = []

        for entry in raw_data:
            ext_name = entry["extractor_name"]
            model_type = entry["type"]
            payload = entry["data"]

            try:
                module = dynamic_load_extractor_module(ext_name)
                ext_instance = module.Extractor()

                model_cls = getattr(module, model_type)
                inner_data = payload.get("data", {})

                obj = model_cls(
                    title=payload["title"],
                    thumbnail=payload["thumbnail"],
                    url=payload["url"],
                    **inner_data,
                    **ext_instance._kwargs_http,
                )
                results.append(obj)

            except Exception as e:
                print(f"Ошибка загрузки {ext_name} ({model_type}): {e}")
                continue

        return results

    # @classmethod
    # def read_config(cls) -> Dict[str, Any]:
    #     path = cls.get_config_path()
    #     text = path.read_text(encoding="utf-8")
    #     data = toml.loads(text)
    #     data["config_path"] = path
    #     return data
