"""Fake Extractor fixture"""


from anicli_ru.base import *
import re


class Anime(BaseAnimeHTTP):
    BASE_URL = "https://example.com/"

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        """Запрос на поиск тайтла по названию.
        Здесь идёт запрос, который выведет результат поиска.

        :param str q: - строка поиска

        :return ResultList[AnimeResult]: - возвращает список объектов AnimeResult"""
        return AnimeResult.parse("")

    def ongoing(self, *args, **kwargs) -> ResultList[BaseOngoing]:
        """Вывод онгоингов
        Здесь идёт запрос, который выведет онгоинги"""
        return Ongoing.parse("")

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]:
        """Вывод доступных эпизодов
        Здесь идёт запрос, который выведет эпизоды с найденного Тайтла/Онгоинга

        :param Union[AnimeResult, Ongoing]: - Объект AnimeResult или Ongoing
        """
        return Episode.parse("")

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:
        """Вывод доступных ссылок на видео.
        Здесь необходимо отправить запрос, на котором присутствуют ссылки на видео"""
        return Player.parse("")


class FakeParser(BaseParser):
    REGEX = {"baz": re.compile(r"baz=(\d+)"),
             "foo": re.compile(r"foo=(.*?)")}
    baz: int
    foo: str


class FakeJsonParser(BaseJsonParser):
    KEYS = ("foo", "bar", "baz")
    foo: str
    bar: int
    baz: int


class AnimeResult(BaseAnimeResult):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile(r"anime_url=(.*?)"),
             "title": re.compile(r"anime_title=(.*?)")}

    url: str
    title: str

    def __str__(self):
        return f"{self.title}"


class Ongoing(BaseOngoing):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile(r"ongoing_url=(.*?)"),
             "title": re.compile(r"ongoing_title=(.*?)"),
             "any_arg": re.compile(r"ongoing_arg=(.*?)")}
    url: str
    title: str
    any_arg: str


class Player(BasePlayer):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile("url (.*?)")}
    url: str

    def __str__(self):
        return


class Episode(BaseEpisode):
    ANIME_HTTP = Anime()
    REGEX = {"ep_num": re.compile(r"ep_num=(.*?)"),
             "ep_name": re.compile(r"ep_name=(.*?)")}

    def __str__(self):
        return ""
