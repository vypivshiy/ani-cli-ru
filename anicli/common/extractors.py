import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import List, Protocol, Type, cast

from anicli_api.base import (
    BaseAnime,
    BaseEpisode,
    BaseExtractor,
    BaseOngoing,
    BaseSearch,
    BaseSource,
)


class ExtractorLikeModule(Protocol):
    Extractor: Type[BaseExtractor]
    Search: Type[BaseSearch]
    Ongoing: Type[BaseOngoing]
    Anime: Type[BaseAnime]
    Episode: Type[BaseEpisode]
    Source: Type[BaseSource]


# guaranteed not will be updated in runtime, cache it for slightly increase speed
@lru_cache(maxsize=1)
def get_extractor_modules(package_name: str = "anicli_api.source") -> List[str]:
    # dynamically get available source extractors
    spec = importlib.util.find_spec(package_name)
    if not spec or not spec.submodule_search_locations:
        return []

    package_path = Path(spec.submodule_search_locations[0])

    # Filter: must be .py, not dunder, not private
    return [
        p.stem.replace("_", "-")
        for p in package_path.glob("*.py")
        if not p.name.startswith("__")
    ]


def dynamic_load_extractor_module(source_name: str) -> ExtractorLikeModule:
    if source_name not in get_extractor_modules():
        msg = f"Extractor module {source_name} not exists in anicli-api"
        raise NameError(msg)
    source_name = source_name.replace("-", "_")
    module = importlib.import_module(f"anicli_api.source.{source_name}")
    module = cast(ExtractorLikeModule, module)
    return module
