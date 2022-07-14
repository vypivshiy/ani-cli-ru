"""Dynamic import extractor form **extractors** directory"""
from typing import cast, Protocol, Type, Tuple, Union
import importlib
from os import PathLike, listdir

from anicli_ru.base import *


class Extractor(Protocol):
    """Typehints dyn imported extractor"""
    Anime: Type[BaseAnimeHTTP]
    AnimeResult: Type[BaseAnimeResult]
    Episode: Type[BaseEpisode]
    Ongoing: Type[BaseOngoing]
    Player: Type[BasePlayer]
    ResultList: Type[ResultList]


def all_extractors(*, absolute_directory: bool = False) -> Tuple[str, ...]:
    if __name__ != "__main__":
        dir_path = __file__.replace(__name__.split(".")[-1] + ".py", "") + "extractors"
    else:
        dir_path = "../../extractors"
    if absolute_directory:
        return tuple("anicli_ru.extractors." + _.replace(".py", "") for _ in listdir(dir_path) if
                     not _.startswith("__") and _.endswith(".py"))

    return tuple(_.replace(".py", "") for _ in listdir(dir_path) if not _.startswith("__") and _.endswith(".py"))


def _validate_module(extractor: Extractor, module_name: Union[PathLike, str]):
    for class_ in ("Anime", "AnimeResult", "Episode", "Ongoing", "Player", "ResultList"):
        try:
            getattr(extractor, class_)
        except AttributeError as exc:
            raise AttributeError(f"Module {module_name} has no class {class_}. Did you import extractor?") from exc


def _import_extractor(module_name: Union[PathLike, str]) -> Extractor:
    try:
        # typehint dynamically import API extractor
        extractor = cast(Extractor, importlib.import_module(str(module_name), package=None))
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Module {module_name} has not founded") from e
    return extractor


def import_extractor(module_name: Union[PathLike, str]) -> Extractor:
    """
    :param module_name: extractor name
    :return: Imported extractor module
    :raise ImportError:
    """
    extractor = _import_extractor(module_name)
    # check extractor scheme
    _validate_module(extractor, module_name)
    return extractor
