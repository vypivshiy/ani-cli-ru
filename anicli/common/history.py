import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import attr

from anicli.common.config import get_history_path
from anicli.common.extractors import dynamic_load_extractor_module

if TYPE_CHECKING:
    from anicli_api.base import BaseSource


def read() -> List[Dict[str, Any]]:
    """Read history from JSON file."""
    path = get_history_path()
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _prepare_entry(
    item: Any,
    extractor_name: str,
    source: Optional[Dict[str, "BaseSource"]] = None,
    episode: str = "Unknown",
) -> Dict[str, Any]:
    """Serialize attr object for storage."""
    full_item_data = attr.asdict(item)
    clean_item_data = {k: v for k, v in full_item_data.items() if not k.startswith("_")}
    source_arr = []
    if source:
        for ep_title, s in source.items():
            full_source_data = attr.asdict(s)
            clean_source_data = {
                k: v for k, v in full_source_data.items() if not k.startswith("_")
            }

            source_arr.append(
                {
                    "episode_title": ep_title,
                    "title": clean_source_data.pop("title", "Unknown"),
                    "url": clean_source_data.pop("url", ""),
                    "data": clean_source_data,
                }
            )

    return {
        "extractor_name": extractor_name,
        "type": item.__class__.__name__,
        "episode": episode,
        "time": None,
        "source": source_arr,
        "data": {
            "title": clean_item_data.pop("title", "Unknown"),
            "thumbnail": clean_item_data.pop("thumbnail", ""),
            "url": clean_item_data.pop("url", ""),
            "data": clean_item_data,
        },
    }


def save(
    item: Any,
    extractor_name: str,
    source: Optional[Dict[str, "BaseSource"]] = None,
    episode: str = "Unknown",
    limit: int = 50,
) -> None:
    """Save item to history with deduplication and limit."""
    entry = _prepare_entry(
        item,
        extractor_name,
        source,
        episode,
    )
    history = read()

    history = [e for e in history if e["data"]["title"] != entry["data"]["title"]]
    history.insert(0, entry)

    with get_history_path().open("w", encoding="utf-8") as f:
        json.dump(history[:limit], f, ensure_ascii=False, indent=4)


def update_last(element: Dict[str, Any]) -> None:
    history = read()
    history[0].update(element)

    with get_history_path().open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


def load() -> List[Any]:
    """Restore extractor objects from history."""
    raw_data = read()
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
            msg = f"Load error {ext_name} ({model_type})"
            raise RuntimeError(msg) from e

    return results


def load_source(entry: Dict[str, Any], episode_title: str) -> "BaseSource":
    """Restore source objects from history."""
    ext_name = entry["extractor_name"]
    model_type = entry["type"]
    sources: List = entry["source"]
    payload = sources[0]
    for s in sources:
        if s["episode_title"] == episode_title:
            payload = s
            break

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
        msg = f"Load error {ext_name} ({model_type})"
        raise RuntimeError(msg) from e
