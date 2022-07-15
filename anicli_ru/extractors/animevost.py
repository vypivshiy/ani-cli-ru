from __future__ import annotations
from typing import Union
import json

from anicli_ru.base import *


class Anime(BaseAnimeHTTP):
    BASE_URL = "https://api.animevost.org/v1/"

    INSTANT_KEY_REPARSE = True

    def api_request(self, *, api_method: str, request_method: str = "GET", **kwargs) -> dict:
        """
        :param str api_method: Animevost api method
        :param str request_method: requests send method type. Default "POST"
        :param kwargs: any requests.Session kwargs
        :return: json response
        """
        resp = self.session.request(request_method, self.BASE_URL + api_method, **kwargs)
        return resp.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search_titles(self, search: str, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, name=search)
        return self.api_request(api_method="search", request_method="POST", data=params, **kwargs)['data']

    def get_updates(self, *, limit: int = 20, **kwargs) -> dict:
        params = self._kwargs_pop_params(kwargs, page=1, quantity=limit)
        return self.api_request(api_method="last", params=params, **kwargs)['data']

    def episode_reparse(self, *args, **kwargs):
        raise NotImplementedError

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        return AnimeResult.parse(self.search_titles(search=q))

    def ongoing(self, *args, **kwargs) -> ResultList[BaseOngoing]:
        return Ongoing.parse(self.get_updates())

    def episodes(self, result: Union[AnimeResult, Ongoing], *args, **kwargs) -> ResultList[BaseEpisode]:  # type: ignore
        req = self.api_request(api_method="playlist", request_method="POST", data={'id': result.id})
        return Episode.parse({"episodes": req, "series": result.series})  # signature fix issue

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:
        raise NotImplementedError("Get this object from Episode object")

    def get_video(self, player_url: str, quality: int = 720, *, referer: str = ""):
        raise NotImplementedError("Get video from Player object")


class Player(BaseJsonParser):
    KEYS = ('key', 'url')
    key: str
    url: str

    def __str__(self):
        return self.key

    def get_video(self, *args, **kwargs) -> str:
        return self.url


class Episode(BaseJsonParser):
    KEYS = ('std', 'preview', 'name', 'hd')
    std: str
    preview: str
    name: str
    hd: str

    @staticmethod
    def sorting_series(series, sort_series):
        name = series.name
        replace = sort_series.replace("\'", "\"")
        jsn = json.loads(replace)
        sort = list(jsn.keys())
        return sort.index(name)

    def __str__(self):
        return self.name

    @classmethod
    def parse(cls, response) -> ResultList:
        """class object factory

        :param response: json response
        :return: ResultList with objects
        """
        # response = sorted(response, key=lambda k: cls.sorting_series(k['name']))
        rez = []
        if isinstance(response["episodes"], list):  # type: ignore
            for data in response["episodes"]:  # type: ignore
                c = cls()
                for k in data.keys():
                    if k in cls.KEYS:
                        setattr(c, k, data[k])
                rez.append(c)
            rez.sort(key=lambda name: cls.sorting_series(name, response["series"]))
        return rez

    def player(self) -> ResultList[Player]:
        rez = []
        rez.extend(Player.parse([{'key': 'hd (720p)', 'url': self.hd},
                                 {'key': 'std (480p)', 'url': self.std}]))
        return rez


class AnimeResult(BaseJsonParser):
    ANIME_HTTP = Anime()
    KEYS = ('id', 'description', 'isFavorite', 'rating', 'series', 'director', 'urlImagePreview', 'year',
            'genre', 'votes', 'title', 'timer', 'type', 'isLikes', 'screenImage')
    id: int
    description: str
    isFavorite: int
    rating: int
    series: dict
    director: str
    urlImagePreview: str
    year: str
    genre: str
    votes: int
    title: str
    timer: int
    type: str
    isLikes: int
    screenImage: list

    def __str__(self):
        return self.title

    def episodes(self):
        with self.ANIME_HTTP as a:
            return a.episodes(self)


class Ongoing(AnimeResult):
    # response equal AnimeResult object
    pass
