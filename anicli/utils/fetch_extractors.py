import os
from importlib import import_module
from importlib.util import find_spec
from typing import List, cast, Type

from anicli_api.base import BaseExtractor

API_PACKAGE_DIR = 'anicli_api.source'


def get_extractor_modules(package_path: str = API_PACKAGE_DIR) -> List[str]:
    """get all available anicli-api extractors"""

    package_path = find_spec(package_path).submodule_search_locations[0]
    files = os.listdir(package_path)
    return [f[:-3] for f in files if f.endswith(".py") and not f.startswith("__") and not f.endswith("__")]


def import_extractor(module_name: str) -> Type['BaseExtractor']:
    """import extractor from anicli_api.source directory in runtime

    raise ModuleNotFoundError if module not found
    """
    module_path = API_PACKAGE_DIR + '.' + module_name
    module = import_module(module_path)
    cast(BaseExtractor, module.Extractor)
    return module.Extractor
