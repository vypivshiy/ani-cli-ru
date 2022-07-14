"""Шаблон для добавления своих парсеров под сторонние сайты

"""
from anicli_ru.base import *
import re


class Anime(BaseAnimeHTTP):
    BASE_URL = "https://example.com"

    def episode_reparse(self, *args, **kwargs):
        # use this method if episodes come first,
        # and then the choice of dubs for the correct operation of the TUI app
        raise NotImplementedError

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        # Entrypoint for searching anime title by string query

        r = self.session.get(self.BASE_URL).text
        return AnimeResult.parse(r)

    def ongoing(self, *args, **kwargs) -> ResultList[BaseOngoing]:
        # Entrypoint for searching ongoings"""
        r = self.session.get(self.BASE_URL).text
        return Ongoing.parse(r)

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]:
        # for get episodes

        # If the source does not need to send HTTP request, do not override this,
        # but call from the object Ongoing|Episode
        r = self.session.get(self.BASE_URL).text
        return Episode.parse(r)

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:
        # Entryponint for get video player url
        # If the source does not need to send HTTP request, do not override this, but call from the object Episode

        r = self.session.get(self.BASE_URL).text
        return Player.parse(r)


class AnimeResult(BaseAnimeResult):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile("foo (.*?)"),
             "title": re.compile("bar (.*?)")}

    url: str
    title: str

    def __str__(self):
        # return output in terminal or str() func
        return f"{self.title}"


class Ongoing(BaseOngoing):
    ANIME_HTTP = Anime()

    def __str__(self):
        return


class Player(BasePlayer):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile("url (.*?)")}
    url: str

    def __str__(self):
        return


class Episode(BaseEpisode):
    ANIME_HTTP = Anime()

    def __str__(self):
        return ""
