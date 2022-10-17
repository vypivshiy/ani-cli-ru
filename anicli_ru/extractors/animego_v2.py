"""new API implementation"""
import dataclasses
import pathlib
from anicli_ru.models import BaseModel, ReField, ReFieldList, ReFieldListDict


@dataclasses.dataclass
class SearchResult:
    title: str
    url: str
    thumbnail: str
    type: str
    year: int

class AnimeInfo(BaseModel):
    """'https://animego.org/anime/* entrypoint"""
    __REGEX__ = (
        ReField(r'<h1>(?P<title>[^<]+)</h1>'),
        ReField(r'Тип</dt><dd class="[^<]+">(?P<type>[^<]+)</dd>'),
        ReField(r'Эпизоды</dt><dd class="[^<]+">(?P<episodes>\d+)</dd>', type_=int, default=1),
        ReField(r'<a href="https://animego\.org/anime/status/(?P<status>[^<]+)" title="[^<]+">[^<]+</a></dd>',
                default="Вышел"),
        ReFieldList(r'<a href="https://animego\.org/anime/genre/(?P<genre>[^<]+)" title="[\w\s\-.]+">[^<]+</a>'),
        ReField(r'Первоисточник</dt><dd class="[^>]+">(?P<source>[^>]+)</dd>',
                name="source"),
        ReField(r'<a href="https://animego\.org/anime/season/\d{4}/\w+">(?P<season>[^>]+)</a>'),
        ReField(r'<a href="https://animego\.org/anime/studio/[^>]+" title="(?P<studio>[^>]+)">'),
        ReField(r'Возрастные ограничения\s*</dt><dd [^>]+><span [^>]+>\s*(?P<age>\d+\+)', type_=int,
                before_func=lambda s: s.rstrip("+")),
        ReField(r'Длительность</dt><dd class=[^>]+>\s*(?P<duration>[^>]+)\s*</dd>',
                after_func=lambda s: s.strip()),
        ReFieldList(r'<a href="/anime/dubbing/[\w\-]+">(?P<dubs>[^>]+)</a>'),
        ReField(r'<a data-ajaximageload class=[^>]+ href="(?P<trailer>[^>]+)" '
                r'data-original="https://img\.youtube\.com/[\w/]+\.[\w]{1,5}"'),
        ReFieldList(r'<a href="https://animego\.org/character/\d+-[^>]+"><span>(?P<characters>[^>]+)</span>'),
        ReFieldList(r'<a class="screenshots-item[^>]*" href="(?P<screenshots>[^>]+\.\w{3,4})"',
                    after_func=lambda s: f"https://animego.org/{s}"),
        ReFieldList(r'class="img-fluid" src="(?P<thumbnails>https?://[^>]+)"'),
        ReField(r'<div class="description [^>]*">\s*(?P<description>.*)\s*</div>',
                before_func=lambda s: s.replace("<br/>", "\n")),
        ReField(r'<span class="rating-value">(?P<rating>[\d,>]+)</span>', type_=float,
                before_func=lambda s: s.replace(",", "."))
    )

    title: str
    type: str
    rating: float
    episodes: int
    status: str
    season: str
    studio: str
    age: int
    genre: list[str]
    source: str
    trailer: str
    dubs: list[str]
    duration: str
    characters: list[str]
    screenshots: list[str]
    thumbnails: list[str]
    description: str


class SearchInfo(BaseModel):
    """https://animego.org/search/anime?q= entrypoint"""
    __REGEX__ = (
        ReFieldListDict(r'data-original="(?P<thumbnail>https://animego\.org/media/[^>]+\.\w{2,4})".*'
                        r'<a href="(?P<url>https://animego\.org/anime/[^>]+)" '
                        r'title="(?P<title>[^>]+)".*'
                        r'href="https://animego\.org/anime/type/[^>]+>(?P<type>[^>]+)<[^>]+.*'
                        r'href="https://animego\.org/anime/season/(?P<year>\d+)',
                        name="info", after_func={"year": lambda i: int(i)}),
    )
    info: list[SearchResult]

    def on_event(self, re_cls):
        print(re_cls.pattern)
        return re_cls

    def middleware(self, re_cls):
        n_lst = [SearchResult(**i) for i in re_cls.value]
        return re_cls.name, n_lst


class OngoingInfo(BaseModel):
    __REGEX__ = (
        ReFieldListDict(r'onclick="location\.href=\'(?P<url>[^>]+)\'.*?url\((?P<thumbnail>[^>]+)\);.*?'
                        r'<span class="[^>]+"><span class="[^>]+">(?P<title>[^>]+)</span>.*?'
                        r'<div class="[^>]+"><div class="[^>]+">(?P<num>[^>]+)'
                        r'</div><div class="[^>]+">\((?P<dub>[^>]+)\)', name="info"),
    )
    info: list[dict[str, str]]


d = pathlib.Path("test_doc2.html").read_text()
ed = SearchInfo(d)
print(ed.dict())
for k, v in ed.dict().items():
    print(k, v)
