from __future__ import annotations
from typing import Union
from anicli_ru.base import *
import re


class Anime(BaseAnimeHTTP):
    BASE_URL = "https://animego.org/"
    _TESTS = {
        "search": ["experiments lain", 13],
        "ongoing": True,
        "search_blocked": False,
        "video": True,
        "search_not_found": "_thisTitleIsNotExist123456",
        "instant": "experiments lain"
    }
    INSTANT_KEY_REPARSE = True

    def search(self, q: str) -> ResultList[AnimeResult]:
        resp = self.request_get(self.BASE_URL + "search/anime", params={"q": q}).text
        return ResultList(AnimeResult.parse(resp))

    def ongoing(self) -> ResultList[Ongoing]:
        resp = self.request_get(self.BASE_URL).text
        return Ongoing.parse(resp)

    def episodes(self, result: Union[AnimeResult, Ongoing]) -> ResultList[Episode]:
        resp = self.request_get(self.BASE_URL + f"anime/{result.id}/player?_allow=true").json()["content"]
        return Episode.parse(resp)

    def players(self, episode: Episode) -> ResultList[Player]:
        resp = self.request_get(self.BASE_URL + "anime/series", params={"dubbing": 2, "provider": 24,
                                                                        "episode": episode.num,
                                                                        "id": episode.id}).json()["content"]
        return Player.parse(resp)


class AnimeResult(BaseAnimeResult):
    REGEX = {"url": re.compile(r'<a href="(https://animego\.org/anime/.*)" title=".*?">'),
             "title": re.compile('<a href="https://animego\.org/anime/.*" title="(.*?)">')}
    ANIME_HTTP = Anime()
    url: str
    title: str

    @property
    def id(self) -> str:
        return self.url.split("-")[-1]

    def __str__(self):
        return f"{self.title}"


class Ongoing(BaseOngoing):
    ANIME_HTTP = Anime()
    REGEX = {
        "raw_url": re.compile(r'onclick="location\.href=\'(.*?)\'"'),
        "title": re.compile(r'600">(.*?)</span></span></div><div class="ml-3 text-right">'),
        "num":
            re.compile(r'<div class="font-weight-600 text-truncate">(\d+) серия</div><div class="text-gray-dark-6">'),
        "dub": re.compile(r'<div class="text-gray-dark-6">(\(.*?\))</div>'),
        "thumbnail": re.compile(r'"background-image: url\((.*?)\);"></div>')
    }

    title: str
    num: str
    dub: str
    raw_url: str

    thumbnail: str

    @classmethod
    def parse(cls, html: str) -> ResultList:
        ongoings = ResultList()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}

        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            ongoings.append(cls(**dict(attrs)))

        # shitty sort duplicates (by title and episode num) algorithm
        # but ongoings list contains less than 100 elements guaranty
        sorted_ongoings = ResultList()
        for ongoing in ongoings:
            if ongoing in sorted_ongoings:
                for sorted_ong in sorted_ongoings:
                    if ongoing == sorted_ong:
                        sorted_ong += ongoing
                        break
            else:
                sorted_ongoings.append(ongoing)

        sorted_ongoings.sort(key=lambda k: k.title)
        return sorted_ongoings

    @property
    def url(self):
        return "https://animego.org" + self.raw_url

    @property
    def id(self) -> str:
        return self.url.split("-")[-1]

    def __eq__(self, other):
        """return True if title name and episode num equals"""
        return self.num == other.num and self.title == other.title and other.dub not in self.dub

    def __iadd__(self, other):
        """Add dub name in ongoing object with += operator"""
        self.dub += f" {other.dub}"
        return self

    def __add__(self, other):
        """Add dub name in ongoing object with + operator"""
        self.dub += f" {other.dub}"
        return self

    def __str__(self):
        return f"{self.title} {self.num} {self.dub}"


class Episode(BaseEpisode):
    ANIME_HTTP = Anime()
    REGEX = {"num": re.compile(r'data-episode="(\d+)"'),
             "id": re.compile(r'data-id="(\d+)"'),
             "name": re.compile(r'data-episode-title="(.*)"')
             }
    num: int
    name: str
    id: int

    def __str__(self):
        return f"{self.name}"


class Player(BasePlayer):
    ANIME_HTTP = Anime()
    REGEX = {
        "dub_name":
            re.compile(
                r'data-dubbing="(\d+)"><span class="video-player-toggle-item-name text-underline-hover">\s+(.*)'),
        "player":
            re.compile(
                r'data-player="(.*?)"\s+data-provider="\d+"\s+data-provide-dubbing="(\d+)"'),
        "dub_id": re.compile(r"")
    }
    _all_raw_player_urls: list
    dub_name: str
    _player: str
    dub_id: int

    @classmethod
    def parse(cls, html: str) -> ResultList:
        l_objects = ResultList()
        # generate dict like {attr_name: list(values)}
        dub_names = re.findall(cls.REGEX["dub_name"], html)  # dub_id, dub_name
        players = re.findall(cls.REGEX["player"], html)  # player_url, dub_id
        for player, dub_id_1 in players:
            p = Player()
            for dub_id_2, dub_name in dub_names:
                # removed check for catching unsupported players
                if dub_id_1 == dub_id_2:
                    p._player, p.dub_name, p.dub_id = player, dub_name, dub_id_1
                    l_objects.append(p)
        return l_objects

    @property
    def url(self) -> str:
        return self.player_prettify(self._player)

    def __str__(self):
        u = self._player.replace("//", "").split(".", 1)[0]
        return f"{self.dub_name} ({u})"
