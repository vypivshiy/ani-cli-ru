from typing import List
from html import unescape

from anicli_api.extractors.base import (
    AnimeHTTP,
    AnimeExtractor,
    BaseSearchResult,
    BaseEpisode,
    BaseOngoing,

)
from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict


class Animego(AnimeHTTP):
    BASE_URL = "https://animego.org/"

    def search(self, query: str, *args, **kwargs) -> str:
        return self.session.get(f"{self.BASE_URL}search/anime", params={"q": query}).text

    def episode(self, url: str, *args, **kwargs):
        anime_id = url.split("-")[-1]
        return unescape(self.session.get(f"https://animego.org/anime/{anime_id}/player",
                                         params={"_allow": "true"}).json()["content"])
        # response_2 = self.session.get(self.BASE_URL + )

    def episode_metadata(self, episode_num: int, episode_id: int):
        resp = self.session.get(f"{self.BASE_URL}anime/series",
                                params={"dubbing": 2, "provider": 24,
                                        "episode": episode_num, "id": episode_id}).json()["content"]
        return unescape(resp)

    def ongoing(self, *args, **kwargs) -> str:
        return self.session.get(self.BASE_URL).text

    def download(self, *args, **kwargs):
        pass


class Extractor(AnimeExtractor):
    HTTP = Animego()

    def search(self, query: str, *args, **kwargs) -> List["SearchResult"]:
        response = self.HTTP.search(query)
        result = ReFieldListDict(r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
                                 r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
                                 r'title="(?P<title>[^>]+)".*'
                                 r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
                                 r'href="https://animego\.org/anime/season/(?P<year>\d+)',
                                 page=response,
                                 name="info",
                                 after_func={"year": lambda i: int(i)})

        return [SearchResult(**kw) for kw in result.value]

    def ongoing(self, *args, **kwargs):
        response = self.HTTP.ongoing()
        result = ReFieldListDict(r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
                                 r'<span class="[^>]+"><span class="[^>]+">(?P<title>[^>]+)</span>.*?'
                                 r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
                                 r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)',
                                 name="info", page=response,
                                 after_func={"url": lambda s: f"https://animego.org{s}"})
        return [Ongoing(**kw) for kw in result.value]

    def download(self, *args, **kwargs):
        pass


class SearchResult(BaseSearchResult):
    HTTP = Animego()
    thumbnail: str
    url: str
    title: str
    type: str
    year: int

    def episodes(self):
        response = self.HTTP.episode(self.url)
        metadata = {
            "title": ReField(r'<h1>(?P<title>[^<]+)</h1>', page=response).value,
            "type": ReField(r'Тип</dt><dd class="[^<]+">(?P<type>[^<]+)</dd>').value,
            "episodes": ReField(r'Эпизоды</dt><dd class="[^<]+">(?P<episodes>\d+)</dd>', type_=int, default=1).value,
            "status": ReField(
                r'<a href="https://animego\.org/anime/status/(?P<status>[^<]+)" title="[^<]+">[^<]+</a></dd>',
                default="Вышел").value,
            "genre": ReFieldList(r'<a href="https://animego\.org/anime/genre/(?P<genre>[^<]+)" '
                                 r'title="[\w\s\-.]+">[^<]+</a>', name="genre").value,
            "source": ReField(r'Первоисточник</dt><dd class="[^>]+">(?P<source>[^>]+)</dd>').value,
            "season": ReField(r'<a href="https://animego\.org/anime/season/\d{4}/\w+">(?P<season>[^>]+)</a>').value,
            "studio": ReField(r'<a href="https://animego\.org/anime/studio/[^>]+" title="(?P<studio>[^>]+)">').value,
            "age": ReField(r'Возрастные ограничения\s*</dt><dd [^>]+><span [^>]+>\s*(?P<age>\d+\+)',
                           type_=int, before_func=lambda s: s.rstrip("+")).value,
            "duration": ReField(r'Длительность</dt><dd class=[^>]+>\s*(?P<duration>[^>]+)\s*</dd>',
                                after_func=lambda s: s.strip()).value,
            "dubs": ReFieldList(r'<a href="/anime/dubbing/[\w\-]+">(?P<dubs>[^>]+)</a>').value,
            "trailer": ReField(r'<a data-ajaximageload class=[^>]+ href="(?P<trailer>[^>]+)" '
                               r'data-original="https://img\.youtube\.com/[\w/]+\.[\w]{1,5}"').value,
            "characters": ReFieldList(
                r'<a href="https://animego\.org/character/\d+-[^>]+"><span>(?P<characters>[^>]+)</span>').value,
            "screenshots": ReFieldList(r'<a class="screenshots-item[^>]*" href="(?P<screenshots>[^>]+\.\w{3,4})"',
                                       after_func=lambda s: f"https://animego.org/{s}").value,
            "thumbnails": ReFieldList(r'class="img-fluid" src="(?P<thumbnails>https?://[^>]+)"').value,
            "description": ReField(r'<div class="description [^>]*">\s*(?P<description>.*)\s*</div>',
                                   before_func=lambda s: s.replace("<br/>", "\n")).value,
            "rating": ReField(r'<span class="rating-value">(?P<rating>[\d,>]+)</span>', type_=float,
                              before_func=lambda s: s.replace(",", ".")).value
        }
        anime_id = self.url.split("-")[-1]
        response_2 = self.HTTP.session.get("")


class Ongoing(BaseOngoing):
    HTTP = Animego()
    url: str
    thumbnail: str
    title: str
    num: str
    dub: str

    def episodes(self):
        response = self.HTTP.episode(self.url)


class Episode(BaseEpisode):
    ...

    def videos(self):
        pass


if __name__ == '__main__':
    ex = Extractor()
    res = ex.search("lain")
    res[0].episodes()
