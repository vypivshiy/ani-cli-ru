from typing import Sequence, Any, Union

from anicli_ru.base import *


class Anime(BaseAnimeHTTP):
    """API method write in snake_case style.
    For details see docs on https://github.com/anilibria/docs/blob/master/api_v2.md"""
    BASE_URL = "https://api.anilibria.tv/v2/"
    INSTANT_KEY_REPARSE = True
    _TESTS = {
        "search": ["Зомбиленд", 12],
        "ongoing": True,
        "search_blocked": False,
        "video": True,
        "search_not_found": "_thisTitleIsNotExist123456",
        "instant": "Зомбиленд"
    }

    def api_request(self, *, api_method: str, request_method: str = "GET", **kwargs) -> dict:
        """
        :param str api_method: Anilibria api method
        :param str request_method: requests send method type. Default "POST"
        :param kwargs: any requests.Session kwargs
        :return: json response
        """
        resp = self.request(request_method, self.BASE_URL + api_method, **kwargs)
        return resp.json()

    @staticmethod
    def _kwargs_pop_params(kwargs, **params) -> dict:
        data = kwargs.pop("params") if kwargs.get("params") else {}
        data.update(params)
        return data

    def search_titles(self, *, search: str, limit: int = -1, **kwargs) -> dict:
        """searchTitles method

        :param search:
        :param limit:
        :param kwargs:
        :return:
        """
        params = self._kwargs_pop_params(kwargs, search=search, limit=limit)
        return self.api_request(api_method="searchTitles", params=params, **kwargs)

    def get_updates(self, *, limit: int = -1, **kwargs) -> dict:
        """getUpdates method

        :param limit:
        :param kwargs:
        :return:
        """
        params = self._kwargs_pop_params(kwargs, limit=limit)
        return self.api_request(api_method="getUpdates", data=params, **kwargs)

    def search(self, q: str) -> ResultList[BaseAnimeResult]:
        return AnimeResult.parse(self.search_titles(search=q))

    def ongoing(self, *args, **kwargs) -> ResultList[BaseOngoing]:
        return Ongoing.parse(self.get_updates())

    def episodes(self, *args, **kwargs) -> ResultList[BaseEpisode]:
        raise NotImplementedError("Get this object from Ongoing or AnimeResult object")

    def players(self, *args, **kwargs) -> ResultList[BasePlayer]:
        raise NotImplementedError("Get this object from Episode object")

    def get_video(self, player_url: str, quality: int = 720, *, referer: str = ""):
        raise NotImplementedError("Get video from Player object")


class BaseJSONParser(BaseParserObject):
    """json parser"""
    REGEX = None
    KEYS: Sequence

    @classmethod
    def parse(cls, response: Union[dict, list[dict]]) -> ResultList:
        rez = ResultList()
        if isinstance(response, list):
            for data in response:
                c = cls()
                for k in data.keys():
                    if k in cls.KEYS:
                        setattr(c, k, data[k])
                rez.append(c)
        elif isinstance(response, dict):
            c = cls()
            for k in response.keys():
                if k in cls.KEYS:
                    setattr(c, k, response[k])
            rez.append(c)
        return rez


class Player(BaseJSONParser):
    KEYS = ('key', 'url')
    key: str
    url: str

    def __str__(self):
        return self.key

    def get_video(self, *args, **kwargs) -> str:
        return self.url


class Episode(BaseJSONParser):
    KEYS = ('serie', 'created_timestamp', 'preview', 'skips', 'hls', 'host')
    host: str  # not used in real API response
    serie: int
    created_timestamp: int
    preview: Any
    skips: dict
    hls: dict

    def __str__(self):
        return f"Episode {self.serie}"

    def player(self) -> ResultList[Player]:
        # {url: str, key: str}
        rez = ResultList()
        for k, v in self.hls.items():
            if v:  # value maybe equal None
                if not self.host.startswith("http"):
                    url = "https://" + self.host + v
                else:
                    url = self.host + v
                rez.extend(Player.parse({"url": url, "key": k}))
        return rez


class AnimeResult(BaseJSONParser):
    KEYS = ('id', 'code', 'names', 'status', 'announce', 'posters', 'updated', 'last_change', 'type',
            'genres', 'team', 'season', 'description', 'in_favorites', 'blocked', 'player', 'torrents')
    id: int
    code: str
    names: dict
    announce: Any
    status: dict
    posters: dict
    updated: int
    last_change: int
    type: dict
    genres: list
    team: dict
    season: dict
    description: str
    in_favorites: int
    blocked: dict
    player: dict
    torrents: dict

    def __str__(self):
        return self.names['ru']

    def episodes(self) -> ResultList[Episode]:
        host = self.player["host"]
        for p in self.player["playlist"].values():
            p["host"] = host
        playlist = [el for el in self.player["playlist"].values()]
        return Episode.parse(playlist)


class Ongoing(AnimeResult):
    # response equal AnimeResult object
    pass
