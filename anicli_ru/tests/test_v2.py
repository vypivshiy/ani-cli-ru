"""
Базовый тест для тестирования парсеров. Тест может проходить довольно долго
(от 5-30 секунд за один парсер), так как посылаются запросы на реальный сайт, без применения monkey path.
Это гарантирует работоспособность парсера как минимум на момент релиза.

В идеальных условиях, парсер должен проходить **все тесты** без переопределения.
Если это не так, то переопределите в классе Anime словарь _TESTS
"""
# TODO добавить аргументы для теста одного выбранного парсера
import warnings
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


def is_video(url):
    return ".m3u8" in url or ".mp4" in url or "sibnet" in url


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_get_search_result(anime: BaseAnimeHTTP):
    """Тест, по поиску тайтла по строке.

    По умолчанию ищет по запросу 'experiments lain' (Эксперименты Лэйн).
    Этот тайтл должен быть гарантированно на сайте. Если это не так и этот парсер должен быть обязательно
    в этом скрипте, то переопределите название.
    """
    print(f" {anime.__module__}")
    query, episodes_count = anime._TESTS.get("search")
    episodes = anime.search(query)[0].episodes()
    # if episodes return first
    assert len(episodes) == episodes_count


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_get_ongoings(anime: BaseAnimeHTTP):
    """Тест, поиска онгоингов

    Для прохождения теста должен найти более 1 онгоингов"""
    print(f" {anime.__module__}")
    if anime._TESTS.get("ongoing"):
        assert len(anime.ongoing()) > 1
    else:
        pytest.skip(f"Ongoings not allowed in {anime.__module__}")


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_get_video(anime: BaseAnimeHTTP):
    """Тест, получения прямой ссылки на видео.

    По умолчанию ищет по запросу 'experiments lain' (Эксперименты Лэйн), берёт первый эпизод и первую ссылку на
    озвучку от (XL Media).
    Этот тайтл должен быть гарантированно на сайте. Если это не так и этот парсер должен быть обязательно
    в этом скрипте, то переопределите этот тест.
    """
    print(f" {anime.__module__}")
    query, episodes_count = anime._TESTS.get("search")
    rez = anime.search(query)
    url = rez[0].episodes()[0].player()[0].get_video()
    assert is_video(url)


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_result_not_found(anime: BaseAnimeHTTP):
    """Тест на гарантированно **не найденный** тайтл"""
    print(f" {anime.__module__}")
    query = anime._TESTS.get("search_not_found")
    assert len(anime.search(query)) == 0


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_get_ongoing_player(anime: BaseAnimeHTTP):
    """Тест на получение объекта эпизода с онгоинга.

    По умолчанию берёт первый и пробует получить ссылку на видео."""
    print(f" {anime.__module__}")
    if anime._TESTS.get("ongoing"):
        for i in range(3):
            ongoing = anime.ongoing()[i]
            episodes = ongoing.episodes()
            if len(episodes) > 0:
                url = episodes[0].player()[0].get_video()
                assert is_video(url)
                return
            if not anime._TESTS.get("search_blocked"):
                pytest.fail(f"Cannot get episodes from {ongoing}. Maybe it block in your country?")
    else:
        pytest.skip(f"Ongoings not allowed in {anime.__module__}")


@pytest.mark.parametrize("anime", ANIME_HTTP_ALL)
def test_instant_run(anime: BaseAnimeHTTP):
    """Test instant run videos. Compare by string"""
    print(f" {anime.__module__}")
    query = anime._TESTS.get("instant")
    result = anime.search(query)[0]
    if anime.INSTANT_KEY_REPARSE:
        names = []
        player_name = str(result.episodes()[0].player()[0])
        for episode in result.episodes()[:3]:
            for player in episode.player():
                if str(player) == player_name:
                    names.append(str(player))
                    break
        assert len(names) == 3
    else:
        pytest.skip("No need to test, INSTANT_KEY_REPARSE == False")


