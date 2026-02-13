# TODO: coming soon
import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, List

import attr
from anicli_api.base import BaseSource

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
    """App configuration and history persistence manager."""

    APP_NAME = "anicliru"

    @classmethod
    def _get_base_dir(cls, env_var: str, default_path: Path) -> Path:
        """Resolve base directory and ensure it exists."""
        base = os.getenv(env_var)
        path = Path(base) if base else default_path
        full_path = path / cls.APP_NAME
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get platform-specific config directory."""
        system = platform.system()
        if system == "Windows":
            return cls._get_base_dir("APPDATA", Path.home() / "AppData" / "Roaming")
        if system == "Darwin":
            return cls._get_base_dir(
                "", Path.home() / "Library" / "Application Support"
            )
        return cls._get_base_dir("XDG_CONFIG_HOME", Path.home() / ".config")

    @classmethod
    def get_data_dir(cls) -> Path:
        """Get platform-specific data directory."""
        system = platform.system()
        if system == "Windows":
            return cls.get_config_dir()
        if system == "Darwin":
            return cls._get_base_dir(
                "", Path.home() / "Library" / "Application Support"
            )
        return cls._get_base_dir("XDG_DATA_HOME", Path.home() / ".local" / "share")

    @classmethod
    def get_config_path(cls) -> Path:
        """Get config.toml path, create default if missing."""
        config = cls.get_config_dir() / "config.toml"
        if not config.exists():
            config.write_text(DEFAULT_CFG, encoding="utf-8")
        return config

    @classmethod
    def get_history_path(cls) -> Path:
        """Get history.json path, create empty if missing."""
        history = cls.get_data_dir() / "history.json"
        if not history.exists():
            history.write_text("[]", encoding="utf-8")
        return history

    @classmethod
    def read_history(cls) -> List[Dict]:
        """Read history from JSON file."""
        path = cls.get_history_path()
        try:
            with path.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    @staticmethod
    def _prepare_history_entry(
        item: Any, source: BaseSource, episode: int, extractor_name: str
    ) -> Dict:
        """Serialize attr object for storage."""
        full_item_data = attr.asdict(item)
        clean_item_data = {
            k: v for k, v in full_item_data.items() if not k.startswith("_")
        }
        full_source_data = attr.asdict(source)
        clean_source_data = {
            k: v for k, v in full_source_data.items() if not k.startswith("_")
        }

        return {
            "extractor_name": extractor_name,
            "type": item.__class__.__name__,
            "episode": episode,
            "time": None,
            "source": {
                "title": clean_source_data.pop("title", "Unknown"),
                "url": clean_source_data.pop("url", ""),
                "data": clean_source_data,
            },
            "data": {
                "title": clean_item_data.pop("title", "Unknown"),
                "thumbnail": clean_item_data.pop("thumbnail", ""),
                "url": clean_item_data.pop("url", ""),
                "data": clean_item_data,
            },
        }

    @classmethod
    def save_history(
        cls,
        item: Any,
        source: BaseSource,
        episode: int,
        extractor_name: str,
        limit: int = 50,
    ):
        """Save item to history with deduplication and limit."""
        entry = cls._prepare_history_entry(item, source, episode, extractor_name)
        history = cls.read_history()

        history = [e for e in history if e["data"]["title"] != entry["data"]["title"]]
        history.insert(0, entry)

        with cls.get_history_path().open("w", encoding="utf-8") as f:
            json.dump(history[:limit], f, ensure_ascii=False, indent=4)

    @classmethod
    def edit_last_history(cls, key: str, value: Any):
        history = cls.read_history()
        history[0][key] = value

        with cls.get_history_path().open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    @classmethod
    def load_history(cls):
        """Restore extractor objects from history."""
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

                kwargs = {
                    **payload.get("data", {}),
                    **ext_instance._kwargs_http,
                    **getattr(ext_instance, "_kwargs_api", {}),
                }

                obj = model_cls(
                    title=payload["title"],
                    thumbnail=payload["thumbnail"],
                    url=payload["url"],
                    **kwargs,
                )
                results.append(obj)
            except Exception as e:
                msg = f"Ошибка загрузки {ext_name} ({model_type})"
                raise RuntimeError(msg) from e

        return results

    @classmethod
    def load_source(cls, entry: Dict[str, Any]):
        """Restore source objects from history."""
        ext_name = entry["extractor_name"]
        model_type = entry["type"]
        payload = entry["source"]

        try:
            module = dynamic_load_extractor_module(ext_name)
            ext_instance = module.Extractor()
            model_cls = module.Source

            kwargs = {
                **payload.get("data", {}),
                **ext_instance._kwargs_http,
                **getattr(ext_instance, "_kwargs_api", {}),
            }

            obj = model_cls(
                title=payload["title"],
                url=payload["url"],
                **kwargs,
            )

            return obj
        except Exception as e:
            msg = f"Ошибка загрузки {ext_name} ({model_type})"
            raise RuntimeError(msg) from e

    # @classmethod
    # def read_config(cls) -> Dict[str, Any]:
    #     path = cls.get_config_path()
    #     text = path.read_text(encoding="utf-8")
    #     data = toml.loads(text)
    #     data["config_path"] = path
    #     return data
