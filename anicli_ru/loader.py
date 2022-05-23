"""Модуль загрузки парсера из директории **extractors**"""
from typing import List, cast, Protocol, Type
import importlib
import os
import sys


from anicli_ru.base import *


class Extractor(Protocol):
    Anime: Type[BaseAnimeHTTP]
    Ongoing: Type[BaseOngoing]
    Episode: Type[BaseEpisode]
    Player: Type[BasePlayer]
    AnimeResult: Type[BaseAnimeResult]
    ResultList: Type[ResultList]


def all_extractors() -> List[str]:
    if __name__ != "__main__":
        dir_path = __file__.replace(__name__.split(".")[-1] + ".py", "") + "extractors"
    else:
        dir_path = "../../extractors"
    return [_.replace(".py", "") for _ in os.listdir(dir_path) if not _.startswith("__") and _.endswith(".py")]


def import_extractor(module_name: str) -> Extractor:
    """
    :param module_name:
    :return: Imported module
    :raise ImportError:
    """
    __import__(module_name)

    if module_name in sys.modules:
        extractor = cast(Extractor, importlib.import_module(module_name))
        return extractor
    raise ImportError("Failed import {} extractor".format(module_name))
