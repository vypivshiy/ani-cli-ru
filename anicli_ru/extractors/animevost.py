from __future__ import annotations
from typing import Union, List
from anicli_ru.base import *
import re

class Anime(BaseAnimeHTTP):
    BASE_URL = "https://v2.vost.pw/"

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        r = self.request_post("https://v2.vost.pw/index.php?do=search", data={"do": "search", "subaction": "search", "story": q})
        # print(r)
        return AnimeResult.parse(r.text)

    def ongoing(self) -> ResultList[Ongoing]:
        r = self.request_get(self.BASE_URL + "ongoing").text
        return Ongoing.parse(r)

    def episodes(self, result: Union[AnimeResult, Ongoing]) -> ResultList[Episode]:
        r = self.request_get("https://api.animevost.org/animevost/api/v0.2/GetInfo/" + str(result.id)).json()["data"][0]["series"]
        return Episode.parse(r)

    def players(self, episode: Episode) -> ResultList[Player]:
        r = self.request_get(self.BASE_URL + "frame5.php", params=dict(play=episode.id, player=9)).text
        return Player.parse(r)


class AnimeResult(BaseAnimeResult):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile(r"<span><a\shref=\"(.*)\"></a></span>\s<h2>.*</h2>"),
             "title": re.compile(r"<span><a\shref=\".*\"></a></span>\s<h2>(.*)</h2>"),
             "id": re.compile(r"<span><a\shref=\"\S*\/(\d*)-.*\"></a></span>")
             }

    url: str
    title: str
    id: str

    @property
    def id(self) -> str:
        return self.id

    def __str__(self):
        return f"{self.title}"


class Ongoing(BaseOngoing):
    ANIME_HTTP = Anime()
    REGEX = {"url": re.compile(r"<span><a\shref=\"(.*)\"></a></span>\s<h2>.*</h2>"),
             "title": re.compile(r"<span><a\shref=\".*\"></a></span>\s<h2>(.*)</h2>"),
             "id": re.compile(r"<span><a\shref=\"\S*\/(\d*)-.*\"></a></span>")
             }

    url: str
    title: str
    id: str

    def id(self) -> str:
        return self.id

    def __str__(self):
        return f"{self.title}"


class Player(BasePlayer):
    ANIME_HTTP = Anime()
    REGEX = {"rez": re.compile(r">(\d{3}p\s\(\w{2}\))</a>"),
             "raw_url": re.compile(r"target=\"_blank\"\shref=\"(.*)\">")
             }
    rez: str
    raw_url: str

    def __str__(self):
        return f"{self.rez}"

    def get_video(self, *args, **kwargs) -> str:
        return self.raw_url

class Episode(BaseEpisode):
    ANIME_HTTP = Anime()
    REGEX = {'num': re.compile(r"'(\d*\(?\d?\)?-?\d*\sсерия)':'\d*'"),
             'id': re.compile(r"'\d*\(?\d?\)?-?\d*\sсерия':'(\d*)'")
             }

    num: str
    id: str

    def id(self) -> str:
        return self.id

    def __str__(self):
        return f"{self.num}"
