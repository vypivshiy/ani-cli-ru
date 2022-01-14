from __future__ import annotations
from typing import Union, List
from anicli_ru.base import BaseAnime, ListObj, BaseObj
from html.parser import unescape
import re


class AnimeResult(BaseObj):
    """
    url str: anime url

    title str: title name
    """
    REGEX = {"url": re.compile(r'<a class="short-poster img-box" href="(.*?\.html)" data-title=".*?: .*?"'),
             "title": re.compile(r'<a class="short-poster img-box" href=".*?\.html" data-title=".*?: (.*?)"')}
    url: str
    title: str

    def __str__(self):
        return f"{self.title}"

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)


class Ongoing(BaseObj):
    """
    title: str title name

    num: str episode number

    url: str url
    """
    REGEX = {
        "raw_url": re.compile(r'<a class="ksupdate_block_list_link" href="(.*?)">.*?</a>'),
        "title": re.compile(r'<a class="ksupdate_block_list_link" href=".*?">(.*?)</a>'),
        "num":
            re.compile(r'<span class="cell cell-2"><a href=".*?">.*?<br>(\d+) .*? </a></span>'),
    }

    title: str
    num: str
    raw_url: str

    @property
    def url(self):
        return "https://animania.online" + self.raw_url

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)

    def __str__(self):
        return f"{self.title} {self.num}"


class Player(BaseObj):
    """
    dub_id int: dubbing ing

    dub_name str: dubbing name

    player str: video player url
    """
    REGEX = {}
    dub_name: str
    _player: str
    dub_id: int
    num: int

    @classmethod
    def parse(cls, html: str) -> ListObj:
        raise NotImplementedError("Get <Player> Object from Episode. Ex: Episode().player()")

    @property
    def url(self) -> str:
        return self._player_prettify(self._player)

    @staticmethod
    def _player_prettify(player: str):
        return "https:" + unescape(player)

    def get_video(self, quality: int = 720, referer: str = "https://animania.online/"):
        with Anime() as a:
            return a.get_video(self.url, quality, referer=referer)

    def __str__(self):
        u = self._player.replace("//", "").split(".", 1)[0]
        return f"{self.num} {self.dub_name} ({u})"


class Episode(BaseObj):
    """
    num: int episode number

    name: str episode name

    id: int episode video id
    """
    REGEX = {
        "video_chunks": re.compile(
            r"""(<li id="season\d+" style="display:none;">(<span onclick="kodikSlider\.player\('.*?', this\);"> .*?</span>){1,})"""),
        "dubs": re.compile(r"""onclick="kodikSlider\.season\('(\d+)', this\)" style="display:none;">(.*?)</span>"""),
        "videos": re.compile(r"""<span onclick="kodikSlider\.player\('(.*?)', this\);">"""),
        "num": re.compile(r'data-episode="(\d+)"'),
        "name": re.compile(r'data-episode-title="(.*)"'),
    }
    dub_id: int
    dub_name: str
    count: int
    videos: List[str]

    def __str__(self):
        return f"{self.dub_name} count: {self.count}"

    def player(self) -> ListObj[Player]:
        _players = ListObj()
        for i, videos in enumerate(self.videos, 1):
            p: Player = Player()
            p.dub_id = self.dub_id
            p.dub_name = self.dub_name
            p._player = videos
            p.num = i
            _players.append(p)
        return _players

    @classmethod
    def parse(cls, html: str) -> ListObj:
        videos_chunks = re.findall(cls.REGEX["video_chunks"], html)
        l_obj = ListObj()
        dubs = re.findall(cls.REGEX["dubs"], html)
        videos = [re.findall(cls.REGEX["videos"], chunk[0]) for chunk in videos_chunks]
        for dub_id, dub_name, count, video in zip([int(n[0]) for n in dubs],  # dub id
                                                  [n[1] for n in dubs],  # dub name
                                                  [len(n) for n in videos],  # count videos
                                                  videos):  # videos urls
            l_obj.append(cls(**{"dub_id": dub_id, "dub_name": dub_name, "count": count, "videos": video}))
        return l_obj

    def __eq__(self, other):
        return self.count == other.count

    def __ge__(self, other):
        return self.count >= other.count

    def __le__(self, other):
        return self.count > other.count


class Anime(BaseAnime):
    BASE_URL = "https://animania.online/index.php"

    def search(self, q: str) -> ListObj[AnimeResult]:
        r = self.request_get(self.BASE_URL, params=dict(do="search", subaction="search", story=q))
        return AnimeResult.parse(r.text)

    def ongoing(self) -> ListObj[Ongoing]:
        r = self.request_get(self.BASE_URL)
        return Ongoing.parse(r.text)

    def episodes(self, result: Union[AnimeResult, Ongoing]) -> ListObj[Episode]:
        r = self.request_get(result.url, headers=self.session.headers.copy().update(
            {"Referer": result.url})
                             )
        return Episode.parse(r.text)

    def players(self):
        # get players from episode object
        raise NotImplementedError


if __name__ == '__main__':
    a = Anime()
    ongs = a.ongoing()
    eps = ongs[0].episodes()
    print()