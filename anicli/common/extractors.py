import importlib.util
import os
from functools import lru_cache
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
    package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]  # type: ignore
    files = os.listdir(package_path)

    # The '-` character is more convenient to type than `_`, no need to hold the key modifier!
    return [
        f[:-3].replace("_", "-") for f in files if f.endswith(".py") and not f.startswith("__") and not f.endswith("__")
    ]


def dynamic_load_extractor_module(source_name: str) -> ExtractorLikeModule:
    source_name = source_name.replace("-", "_")
    if source_name not in get_extractor_modules():
        msg = f"Extractor module {source_name} not exists in anicli-api"
        raise NameError(msg)
    module = importlib.import_module(f"anicli_api.source.{source_name}")
    module = cast(ExtractorLikeModule, module)
    return module
