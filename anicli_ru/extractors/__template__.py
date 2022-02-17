"""Шаблон для добавления своих парсеров под сторонние сайты

"""
from typing import Union, List
from anicli_ru.base import BaseAnimeHTTP, ResultList, BaseAnimeResult, BasePlayer, BaseOngoing, BaseEpisode
import re


class AnimeResult(BaseAnimeResult):
    REGEX = {"url": re.compile("foo (.*?)"),
             "title": re.compile("bar (.*?)")}

    url: str
    title: str

    def __str__(self):
        return f"{self.title}"

    def episodes(self):
        pass


class Ongoing(BaseOngoing):
    REGEX = {}

    def __str__(self):
        return

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)


class Player(BasePlayer):
    REGEX = {"url": re.compile("url (.*?)")}
    url: str

    def __str__(self):
        return

    def get_video(self, quality: int = 720, referer: str = "https://example.com/"):
        with Anime() as a:
            return a.get_video(self.url, quality, referer=referer)


class Episode(BaseEpisode):
    REGEX = {}

    def __str__(self):
        return ""

    def player(self):
        with Anime() as a:
            return a.players(self)


class Anime(BaseAnimeHTTP):
    BASE_URL = "https://example.com"

    def search(self, q: str) -> ResultList[AnimeResult]:
        """Запрос на поиск тайтла по названию.
        Здесь идёт запрос, который выведет результат поиска.

        :param str q: - строка поиска

        :return ResultList[AnimeResult]: - возвращает список объектов AnimeResult"""

    def ongoing(self) -> ResultList[Ongoing]:
        """Вывод онгоингов
        Здесь идёт запрос, который выведет онгоинги"""

    def episodes(self, result: Union[AnimeResult, Ongoing]) -> ResultList[Episode]:
        """Вывод доступных эпизодов
        Здесь идёт запрос, который выведет эпизоды с найденного Тайтла/Онгоинга

        :param Union[AnimeResult, Ongoing]: - Объект AnimeResult или Ongoing
        """

    def players(self, episode: Episode) -> ResultList[Player]:
        """Вывод доступных ссылок на видео.
        Здесь необходимо отправить запрос, на котором присутствуют ссылки на видео"""
