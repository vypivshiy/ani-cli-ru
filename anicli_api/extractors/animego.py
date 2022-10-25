"""THIS EXTRACTOR WORKS ONLY MOBILE USERAGENT!!!

Example:
    >>> extractor = Extractor()
    >>> search_results = extractor.search("lain")  # search
    >>> anime = search_results[0].anime()  # get first title (Serial of experiments lain)
    >>> episodes = anime.episodes()  # get all episodes
    >>> videos = episodes[0].videos() # get available video object
    >>> videos[0].link()  # get direct links
    >>> ongoings = extractor.ongoing()  # get ongoings
    >>> anime = ongoings[0].anime()  # get first ongoing
    >>> # ... equal upper :)
"""
from typing import List, Optional

from anicli_api.extractors.base import (
    AnimeHTTP,
    AnimeExtractor,
    BaseSearchResult,
    BaseEpisode,
    BaseOngoing,
    BaseAnimeInfo,
    BaseVideo
)

from anicli_api.decoders import Kodik, Aniboom

from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many


class Animego(AnimeHTTP):
    BASE_URL = "https://animego.org/"

    def search(self, query: str, *args, **kwargs) -> str:
        return self.session.get(f"{self.BASE_URL}search/anime", params={"q": query}).text

    def episode(self, url: str, *args, **kwargs):
        anime_id = url.split("-")[-1]
        return self.unescape(self.session.get(f"https://animego.org/anime/{anime_id}/player",
                                              params={"_allow": "true"}).json()["content"])

    def episode_metadata(self, episode_num: int, episode_id: int):
        resp = self.session.get(f"{self.BASE_URL}anime/series",
                                params={"dubbing": 2, "provider": 24,
                                        "episode": episode_num, "id": episode_id}).json()["content"]

        return self.unescape(resp)

    def ongoing(self, *args, **kwargs) -> str:
        return self.session.get(self.BASE_URL).text

    def download(self, *args, **kwargs):
        pass

    def anime(self, url: str, *args, **kwargs):
        return self.unescape(self.session.get(url).text)


class Extractor(AnimeExtractor):
    HTTP = Animego()

    def search(self, query: str, *args, **kwargs) -> List["SearchResult"]:
        response = self.HTTP.search(query)
        result = ReFieldListDict(r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
                                 r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
                                 r'title="(?P<title>[^>]+)".*'
                                 r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
                                 r'href="https://animego\.org/anime/season/(?P<year>\d+)',
                                 name="info",
                                 after_exec_type={"year": lambda i: int(i)}).parse(response)

        return [SearchResult(**data) for data in result["info"]]

    def ongoing(self, *args, **kwargs):
        response = self.HTTP.ongoing()
        result = ReFieldListDict(r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
                                 r'<span class="[^>]+"><span class="[^>]+">(?P<title>[^>]+)</span>.*?'
                                 r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
                                 r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)',
                                 name="info",
                                 after_exec_type={"url": lambda s: f"https://animego.org{s}"}).parse(response)
        return [Ongoing(**data) for data in result["info"]]

    def download(self, *args, **kwargs):
        pass


class SearchResult(BaseSearchResult):
    HTTP = Animego()
    thumbnail: str
    url: str
    title: str
    type: str
    year: int

    def anime(self) -> "AnimeInfo":
        response = self.HTTP.anime(self.url)
        metadata = parse_many(response,
                              ReField(r'ratingValue":"(?P<rating>[\d\.]+)"',
                                      type=float,
                                      default=0),
                              ReField(r'"numberOfEpisodes":(?P<max_count>\d+),',
                                      type=int,
                                      default=1),
                              ReField(r'"startDate":"(?P<date>\d{4}-\d{2}-\d{2})"'),
                              ReField(r'"genre":\[(.*?)\],"',
                                      name="genres",
                                      after_exec_type=lambda s: s.strip('"').split(","),  # list[str] genres
                                      ),
                              ReField(r'"alternativeHeadline":\[(.*?)\],"',
                                      name="alternative_headlines",
                                      after_exec_type=lambda s: s.strip('"').split(",")),  # list[str]
                              ReFieldList(r'/person.*?,"name":"([\w\s]+)"}', name="actors"),
                              ReField(r'@type":"Organization".*?"name":"(?P<studio>[^>]+)"'),
                              ReField(r'<div class="anime-title"><div><h1>(?P<title>[^>]+)</h1>'),
                              ReField(r'Первоисточник</dt><dd [^>]+>(?P<source>[^>]+)</dd>'),
                              ReField(r'>Сезон</dt><dd [^>]+><a href=[^>]+>(?P<season>[^>]+)</a>'),
                              ReField(r'<div data-readmore="content">(?P<description>[^>]+)<'),
                              ReFieldList(r'<a class="screenshots-item ml-3" href="([^>]+)" data',
                                          name="screenshots",
                                          after_exec_type=lambda s: f"https://animego.org{s}"),
                              ReFieldList(r'class="img-fluid" src="([^>]+)"',
                                          name="thumbnails"),
                              ReField(r'Возрастные ограничения[^>]+><dd[^>]+>[^>]+>[^>]+(?P<age>\d+)\+',
                                      type=int),
                              ReField(r'Длительность[^>]+>[^>]+>\s*(?P<duration>[^>]+)<',
                                      after_exec_type=lambda s: s.strip()),
                              ReFieldList(r'href="/anime/dubbing/[^>]+">(?P<dubs>[^>]+)</a>',
                                          name="dubs"),
                              )
        return AnimeInfo(url=self.url, **metadata)


class Ongoing(BaseOngoing):
    HTTP = Animego()
    url: str
    thumbnail: str
    title: str
    num: str
    dub: str

    def anime(self) -> "AnimeInfo":
        response = self.HTTP.anime(self.url)
        metadata = parse_many(response,
                              ReField(r'ratingValue":"(?P<rating>[\d\.]+)"',
                                      type=float,
                                      default=0),
                              ReField(r'"startDate":"(?P<date>\d{4}-\d{2}-\d{2})"'),
                              ReFieldList(r'<a href="https?:[\w\-\./]+/genre/[\w\-\.]+" title="([\w\-]+)">',
                                          name="genres",
                                          after_exec_type=lambda s: s.rstrip().rstrip(".")),
                              ReFieldList(r'<li>([^>]+)</li>{1,15}', name="alternative_headlines"),
                              ReField(r'@type":"Organization".*?"name":"(?P<studio>[^>]+)"'),
                              ReField(r'<div class="anime-title"><div><h1>(?P<title>[^>]+)</h1>'),
                              ReField(r'Первоисточник</dt><dd [^>]+>(?P<source>[^>]+)</dd>'),
                              ReField(r'>Сезон</dt><dd [^>]+><a href=[^>]+>(?P<season>[^>]+)</a>'),
                              ReField(r'<div data-readmore="content">(?P<description>[^>]+)<',
                                      after_exec_type=lambda s: s.strip().rstrip("&hellip;")),
                              ReFieldList(r'<a class="screenshots-item[^>]+ href="([^>]+)" data-ajax',
                                          name="screenshots",
                                          after_exec_type=lambda s: f"https://animego.org{s}"),
                              ReFieldList(r'class="img-fluid" src="([^>]+)"',
                                          name="thumbnails"),
                              ReField(r'Возрастные ограничения[^>]+><dd[^>]+>[^>]+>\s*(?P<age>\d+)\+',
                                      type=int,
                                      default=0),
                              ReField(r'Длительность[^>]+>[^>]+>\s*(?P<duration>[^>]+)<',
                                      after_exec_type=lambda s: s.strip()),
                              )

        return AnimeInfo(url=self.url, **metadata)


class AnimeInfo(BaseAnimeInfo):
    HTTP = Animego()
    url: str
    rating: float
    date: str
    alternative_headlines: List[str]
    studio: Optional[str]
    title: str
    source: str
    season: str
    description: str
    screenshots: List[str]
    thumbnails: List[str]
    age: int
    duration: str

    def episodes(self) -> List["Episode"]:
        response = self.HTTP.episode(self.url)
        episodes = ReFieldListDict(r'''data-episode="(?P<num>\d+)"
        \s*data-id="(?P<id>\d+)"
        \s*data-episode-type="(?P<type>.*?)"
        \s*data-episode-title="(?P<title>.*?)"
        \s*data-episode-released="(?P<released>.*?)"
        \s*data-episode-description="(?P<description>.*?)"''',
                                   name="episodes",
                                   after_exec_type={
                                       "num": int,
                                       "id": int,
                                       "type": int}).parse_values(response)
        return [Episode(url=self.url, **ep) for ep in episodes]


class Episode(BaseEpisode):
    HTTP = Animego()
    id: int
    num: int
    type: int
    title: str
    released: str
    description: str
    url: str

    def videos(self):
        resp = self.HTTP.episode_metadata(self.num, self.id)
        dubs = ReFieldListDict(r'data-dubbing="(?P<dub_id>\d+)"><span [^>]+>\s*(?P<dub>[\w\s\-]+)\n',
                               name="dubs",
                               after_exec_type={"id": int}).parse_values(resp)
        videos = ReFieldListDict(r'player="(?P<url>//[\w/\.\?&;=]+)"[^>]+data-[\w\-]+="(?P<dub_id>\d+)">'  # kodik data-provider
                                 r'<span[^>]+>(?P<name>[^>]+)<',  # aniboom - data-provide-dubbing
                                 name="videos",
                                 after_exec_type={"id": int,
                                                  "url": lambda u: f"https:{u}"}).parse_values(resp)
        result = []
        for video in videos:
            result.extend({**dub, **video} for dub in dubs if video["dub_id"] == dub["dub_id"])
        return [Video(**vid) for vid in result]


class Video(BaseVideo):
    dub_id: int
    url: str
    dub: str
    name: str

    def link(self):
        if self.url == Kodik():
            return Kodik.parse(self.url)
        elif self.url == Aniboom():
            return Aniboom.parse(self.url)
        return self.url


if __name__ == '__main__':
    # example get all series Serial of experiments Lain
    ex = Extractor()
    res = ex.search("lain")  # search
    ani = res[0].anime()  # get anime metadata
    print(ani.title, ani.rating, ani.duration)
    print(ani.description)
    print(ani.screenshots)
    eps = ani.episodes()
    for ep in eps[:3]:
        vi = ep.videos()
        print(vi[0].dub, vi[0].link())

    # example get first ongoing videos:
    ongs = ex.ongoing()
    ani = ongs[0].anime()
    print(ani.title, ani.rating, ani.duration)
    print(ani.description)
    print(ani.screenshots)
    eps = ani.episodes()
    for ep in eps[:2]:
        vi = ep.videos()
        for v in vi:
            print(v.dub, v.link())
