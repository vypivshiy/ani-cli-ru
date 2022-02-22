"""Модуль загрузки парсера из директории **extractors**"""
from typing import List
import os
import sys


def all_extractors() -> List[str]:
    if __name__ != "__main__":
        dir_path = __file__.replace(__name__.split(".")[-1] + ".py", "") + "extractors"
    else:
        dir_path = "../../extractors"
    return [_.replace(".py", "") for _ in os.listdir(dir_path) if not _.startswith("__") and _.endswith(".py")]


def import_extractor(module_name: str):
    """
    :param module_name:
    :return: Imported module
    :raise ImportError:
    """
    __import__(module_name)

    if module_name in sys.modules:
        return sys.modules[module_name]
    raise ImportError("Failed import {} extractor".format(module_name))
