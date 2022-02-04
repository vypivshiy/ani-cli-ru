"""Load available parsers"""
import importlib.util
from typing import List
import os
import sys


def all_extractors() -> List[str]:
    if __name__ != "__main__":
        dir_path = __file__.replace(__name__.split(".")[-1] + ".py", "") + "extractors"
    else:
        dir_path = "extractors"
    return [_.replace(".py", "") for _ in os.listdir(dir_path) if not _.startswith("__") and _.endswith(".py")]


def import_extractor(name):
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module

