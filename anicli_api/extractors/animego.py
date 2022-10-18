from dataclasses import dataclass
from typing import List

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

    def episode(self, *args, **kwargs):
        pass

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
        pass


class Ongoing(BaseOngoing):
    HTTP = Animego()
    url: str
    thumbnail: str
    title: str
    num: str
    dub: str

    def episodes(self):
        pass


if __name__ == '__main__':
    ex = Extractor()
    res = ex.search("lain")
    ongs = ex.ongoing()
    print(res[0].dict())
    print(*ongs, sep="\n")
