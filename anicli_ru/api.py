from __future__ import annotations
from html import unescape
from typing import Union
from anicli_ru.base import ListObj, BaseObj, BaseAnime
import re


class AnimeResult(BaseObj):
    """
    url str: anime url

    title str: title name
    """
    REGEX = {"url": re.compile(r'<a href="(https://animego\.org/anime/.*)" title=".*?">'),
             "title": re.compile('<a href="https://animego\.org/anime/.*" title="(.*?)">')}
    url: str
    title: str

    @property
    def id(self) -> str:
        return self.url.split("-")[-1]

    def __str__(self):
        return f"{self.title}"

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)


class Ongoing(BaseObj):
    """
    title: str title name

    num: str episode number

    dub: str dubbing name

    url: str url
    """
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
    def parse(cls, html: str) -> ListObj:
        ongoings = ListObj()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}

        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            ongoings.append(cls(**dict((k, v) for k, v in attrs)))

        # shitty sort duplicates (by title and episode num) algorithm
        # but ongoings list contains less than 100 elements guaranty
        sorted_ongoings = ListObj()
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

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)

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


class Episode(BaseObj):
    """
    num: int episode number

    name: str episode name

    id: int episode video id
    """
    REGEX = {"num": re.compile(r'data-episode="(\d+)"'),
             "id": re.compile(r'data-id="(\d+)"'),
             "name": re.compile(r'data-episode-title="(.*)"'),
             }
    num: int
    name: str
    id: int

    def __str__(self):
        return f"{self.name}"

    def player(self):
        with Anime() as a:
            return a.players(self)


class Player(BaseObj):
    """
    dub_id int: dubbing ing

    dub_name str: dubbing name

    player str: video player url
    """
    REGEX = {
        "dub_name":
            re.compile(
                r'data-dubbing="(\d+)"><span class="video-player-toggle-item-name text-underline-hover">\s+(.*)'),
        "player":
            re.compile(
                r'data-player="(.*?)"\s+data-provider="\d+"\s+data-provide-dubbing="(\d+)"'),
        "dub_id": re.compile(r"")
    }
    dub_name: str
    _player: str
    dub_id: int

    @classmethod
    def parse(cls, html: str) -> ListObj:
        l_objects = ListObj()
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
        return self._player_prettify(self._player)

    @staticmethod
    def _player_prettify(player: str):
        return "https:" + unescape(player)

    def get_video(self, quality: int = 720, referer: str = "https://animego.org/"):
        with Anime() as a:
            return a.get_video(self.url, quality, referer=referer)

    def __str__(self):
        u = self._player.replace("//", "").split(".", 1)[0]
        return f"{self.dub_name} ({u})"


class Anime(BaseAnime):
    """Anime class parser

    :example:

    ```python
    a = Anime()
    results = a.search("school")
    results.print_enumerate()
    episodes = results[0].episodes()
    ```
    """
    BASE_URL = "https://animego.org"

    # mobile user-agent can sometimes gives a chance to bypass the anime title ban
    USER_AGENT = {"user-agent":
                      "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
                  "x-requested-with": "XMLHttpRequest"}

    def search(self, q: str) -> ListObj[AnimeResult]:
        """Get search results

        :param str q: search query
        :return: anime results list
        :rtype: ListObj
        """
        resp = self.request_get(self.BASE_URL + "/search/anime", params={"q": q}).text
        return ListObj(AnimeResult.parse(resp))

    def ongoing(self) -> ListObj[Ongoing]:
        """Get ongoings

        :return: ongoings results list
        :rtype: ListObj
        """
        resp = self.request_get(self.BASE_URL).text
        return Ongoing.parse(resp)

    def episodes(self, result: Union[AnimeResult, Ongoing]) -> ListObj[Episode]:
        """Get available episodes

        :param result: Ongoing or AnimeSearch object
        :return: list available episodes
        :rtype: ListObj
        """
        resp = self.request_get(self.BASE_URL + f"/anime/{result.id}/player?_allow=true").json()["content"]
        return Episode.parse(resp)

    def players(self, episode: Episode) -> ListObj[Player]:
        """Return video players urls

        :param Episode episode: Episode object
        :return: list available players
        :rtype: ListObj[Player]
        """
        resp = self.request_get(self.BASE_URL + "/anime/series", params={"dubbing": 2, "provider": 24,
                                                                         "episode": episode.num,
                                                                         "id": episode.id}).json()["content"]
        players = Player.parse(resp)
        return players
