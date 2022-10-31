"""THIS EXTRACTOR WORKS ONLY MOBILE USERAGENT!!!

Example:
    >>> extractor = Extractor()
    >>> search_results = extractor.search("lain")  # search
    >>> anime = search_results[0].get_anime()  # get first title (Serial of experiments lain)
    >>> episodes = anime.get_episodes()  # get all episodes
    >>> videos = episodes[0].get_videos() # get available video object
    >>> videos[0].get_source()  # get direct links
    >>> ongoings = extractor.ongoing()  # get ongoings
    >>> anime = ongoings[0].get_anime()  # get first ongoing
    >>> # ... equal upper :)
"""

from typing import List, Optional

from anicli_api.extractors.base import (
    AnimeExtractor,
    BaseSearchResult,
    BaseEpisode,
    BaseOngoing,
    BaseAnimeInfo,
    BaseVideo,
    BaseModel,
    TypeSearch
)


class Extractor(AnimeExtractor):
    BASE_URL = "https://animego.org/"

    def search(self, query: str) -> List[TypeSearch]: #List["SearchResult"]:
        response = self.HTTP.get(f"{self.BASE_URL}search/anime", params={"q": query}).text
        result = self._ReFieldListDict(
            r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
            r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
            r'title="(?P<name>[^>]+)".*'
            r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
            r'href="https://animego\.org/anime/season/(?P<year>\d+)',
            name="info",
            after_exec_type={"year": lambda i: int(i)}).parse_values(response)
        # {thumbnail:str, url: str, name: str, type: str, year: int}
        return [SearchResult(**data) for data in result]

    async def async_search(self, query: str) -> List['SearchResult']:
        ...

    async def async_ongoing(self) -> List['Ongoing']:
        ...

    def ongoing(self):
        response = self.HTTP.get(self.BASE_URL)
        result = self._ReFieldListDict(
            r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
            r'<span class="[^>]+"><span class="[^>]+">(?P<name>[^>]+)</span>.*?'
            r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
            r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)',
            name="info",
            after_exec_type={"url": lambda s: f"https://animego.org{s}",
                             "num": int}).parse_values(response)
        # {url: str, thumbnail: str, name: str, num: int, dub: str}
        return [Ongoing(**data) for data in result]

    def iter_ongoing(self):
        ongoings = self.ongoing()
        for ong in ongoings:
            anime = ong.get_anime()
            for episode in anime.get_episodes():
                for video in episode.get_videos():
                    yield {
                        "ongoing": ong.dict(),
                        "anime": anime.dict(),
                        "episode": episode.dict(),
                        "video_meta": video.dict(),
                        "video": video.get_source()
                    }


class AnimeParser(BaseModel):
    """avoid duplicate code"""
    url: str

    _DECODE_TABLE = {
        "Тип": "type",
        "Эпизоды": "episodes",
        "Статус": "status",
        "Жанр": "genres",
        "Первоисточник": "source",
        "Сезон": "season",
        "Выпуск": "release",
        "Студия": "studio",
        "Рейтинг MPAA": "mpaa",
        "Возрастные ограничения": "age",
        "Длительность": "length",
        "Озвучка": "dubs",
        "Автор оригинала": "author",
        "Главные герои": "characters"
    }

    @classmethod
    def _decode_table(cls, table: dict):
        return {cls._DECODE_TABLE.get(k): table[k] for k in table if cls._DECODE_TABLE.get(k)}

    @classmethod
    def _soup_extract_table(cls, soup):
        keys, values = [], []
        # get from table metadata
        for el in soup.find("dl", attrs={"class": "row"}).find_all("dt"):
            key = el.get_text(strip=True)
            value = el.find_next("dd").get_text(strip=True)
            keys.append(key)
            values.append(value)
        # convert keys to latin
        return cls._decode_table(dict(zip(keys, values)))

    def get_anime(self) -> "AnimeInfo":
        response = self.HTTP.get(self.url).text
        soup = self._soup(response)
        meta = self._soup_extract_table(soup)

        meta["name"] = soup.find("div", attrs={"class": "anime-title"}).find_next("h1").get_text()
        meta["alt_names"] = [
            t.get_text(strip=True) for t in soup.find("div", attrs={"class": "synonyms"}).find_all("li")]
        meta["rating"] = float(soup.find("span", class_="rating-value").get_text(strip=True).replace(",", "."))
        meta["description"] = soup.find("div", attrs={"data-readmore": "content"}).get_text(strip=True)
        meta["genres"] = meta.get("genres").split(",")
        meta["id"] = self.url.split("-")[-1]
        meta["screenshots"] = self._ReFieldList(
            r'<a class="screenshots-item[^>]+" href="([^>]+)" data-ajax',
            name="screenshots",
            after_exec_type=lambda s: f"https://animego.org{s}").parse_values(response)
        meta["thumbnails"] = self._ReFieldList(
            r'class="img-fluid" src="([^>]+)"',
            name="a").parse_values(response)
        meta["dubs"] = meta.get("dubs").split(",") if meta.get("dubs") else []
        meta["url"] = self.url
        return AnimeInfo(**meta)

    async def a_get_anime(self):
        ...


class SearchResult(AnimeParser, BaseSearchResult):
    url: str
    name: str
    type: str
    # extra metadata
    year: int
    thumbnail: str


class Ongoing(AnimeParser, BaseOngoing):
    url: str
    name: str
    num: int

    # meta
    thumbnail: str
    dub: str


class AnimeInfo(BaseAnimeInfo):
    id: str
    url: str
    # meta
    type: str
    episodes: str
    status: str
    genres: List[str]
    source: str
    season: str
    release: str
    studio: str
    mpaa: str
    age: str
    length: str
    dubs: Optional[List[str]]
    author: str
    characters: str
    name: str
    alt_names = List[str]
    rating: float
    description: str
    screenshots: List[str]
    thumbnails: List[str]

    def get_episodes(self) -> List["Episode"]:
        response = self.HTTP.get(f"https://animego.org/anime/{self.id}/player",
                                 params={"_allow": "true"}).json()["content"]
        episodes = self._ReFieldListDict(
            r'''data-episode="(?P<num>\d+)"
        \s*data-id="(?P<id>\d+)"
        \s*data-episode-type="(?P<type>.*?)"
        \s*data-episode-title="(?P<name>.*?)"
        \s*data-episode-released="(?P<released>.*?)"
        \s*data-episode-description="(?P<description>.*?)"''',
            name="episodes",
            after_exec_type={"num": int, "id": int, "type": int}).parse_values(response)
        return [Episode(url=self.url, **ep) for ep in episodes]


class Episode(BaseEpisode):
    id: int
    num: int
    # meta
    type: int
    name: str
    released: str
    description: str
    url: str

    def get_videos(self):
        resp = self.HTTP.get("https://animego.org/anime/series",
                             params={"dubbing": 2,
                                     "provider": 24,
                                     "episode": self.num, "id": self.id}).json()["content"]

        dubs = self._ReFieldListDict(
            r'data-dubbing="(?P<dub_id>\d+)"><span [^>]+>\s*(?P<dub>[\w\s\-]+)\n',
            name="dubs",
            after_exec_type={"id": int}).parse_values(resp)

        videos = self._ReFieldListDict(
            r'player="(?P<url>//[\w/\.\?&;=]+)"'
            r'[^>]+data-[\w\-]'  # aniboom - data-provide-dubbing kodik  - data-provider strings
            r'+="(?P<dub_id>\d+)"><span[^>]+>(?P<name>[^>]+)<',
            name="videos",
            after_exec_type={"id": int,
                             "url": lambda u: f"https:{u}"}).parse_values(resp)
        result = []
        for video in videos:
            result.extend({**dub, **video} for dub in dubs if video["dub_id"] == dub["dub_id"])
        return [Video(**vid) for vid in result]


class Video(BaseVideo):
    url: str
    # meta
    # dub_id: int
    # dub: str
    # name: str


if __name__ == '__main__':
    # example get all series Serial of experiments Lain
    ex = Extractor()
    res = ex.search("lain")
    res[0].get_anime()
