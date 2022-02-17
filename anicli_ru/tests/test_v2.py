"""
Базовый тест для тестирования парсеров. Тест может проходить довольно долго
(от 5-30 секунд за один парсер), так как посылаются запросы на реальный сайт, без подмены ответов.
Это гарантирует работоспособность парсера как минимум на момент релиза.

В идеальных условиях, парсер должен проходить **все тесты** без переопределения тестов.
"""

from sys import modules as sys_modules

from anicli_ru import loader
from anicli_ru.base import BaseAnimeHTTP
import pytest


IMPORTED_MODULES = []

extractors = loader.all_extractors()
for m in ["anicli_ru.extractors." + m for m in extractors]:
    __import__(m)
    if m not in sys_modules:
        raise ImportError("Failed import {} extractor".format(m))
    IMPORTED_MODULES.append(sys_modules[m])
    print("LOAD", m)

ANIME_HTTP_ALL = [p.Anime() for p in IMPORTED_MODULES]


@pytest.mark.parametrize("anime,q", [(p, "experiments lain") for p in ANIME_HTTP_ALL])
def test_get_search_result(anime: BaseAnimeHTTP, q: str):
    """Тест, по поиску тайтла по строке.

    По умолчанию ищет по запросу 'experiments lain' (Эксперименты Лэйн).
    Этот тайтл должен быть гарантированно на сайте. Если это не так и этот парсер должен быть обязательно
    в этом скрипте, то переопределите этот тест.

    :param str q: - поисковый запрос тайтла. По умолчанию experiments lain.
    """
    print(f" Run {anime.__module__}")
    episodes = anime.search(q)[0].episodes()
    # if episodes return first
    if len(episodes) == 13:
        assert len(episodes) == 13
    # else return dubs first
    else:
        assert len(episodes) == 1


@pytest.mark.parametrize("anime", list(ANIME_HTTP_ALL))
def test_get_ongoings(anime: BaseAnimeHTTP):
    """Тест, поиска онгоингов

    Для прохождения теста должен найти более 1 онгоингов"""
    print(f" Run {anime.__module__}")
    rez = anime.ongoing()
    assert len(rez) > 1


@pytest.mark.parametrize("anime,q", [(p, "experiments lain") for p in ANIME_HTTP_ALL])
def test_get_video(anime: BaseAnimeHTTP, q: str):
    """Тест, получения прямой ссылки на видео.

    По умолчанию ищет по запросу 'experiments lain' (Эксперименты Лэйн), берёт первый эпизод и первую ссылку на
    озвучку от (XL Media).
    Этот тайтл должен быть гарантированно на сайте. Если это не так и этот парсер должен быть обязательно
    в этом скрипте, то переопределите этот тест.

    :param str q: - поисковый запрос тайтла. По умолчанию experiments lain"""
    print(f" Run {anime.__module__}")
    rez = anime.search(q)
    url = rez[0].episodes()[0].player()[0].get_video()
    assert ".m3u8" in url or ".mp4" in url or "sibnet" in url


@pytest.mark.parametrize("anime,title_name", [(p, "_thisTitleIsNotExist123456") for p in ANIME_HTTP_ALL])
def test_result_not_found(anime: BaseAnimeHTTP, title_name: str):
    """Тест на гарантированно не найденный тайтл"""
    print(f" Run {anime.__module__}")
    rez = anime.search(title_name)
    assert len(rez) == 0


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_get_ongoing_player(anime: BaseAnimeHTTP):
    """Тест на получение объекта эпизода с онгоинга.
    По умолчанию берёт первый и пробует получить ссылку на видео."""
    print(f" Run {anime.__module__}")
    url = anime.ongoing()[0].episodes()[0].player()[0].get_video()
    assert ".m3u8" in url or ".mp4" in url or "sibnet" in url
