import re
from html import unescape
from collections import UserList
from typing import Union

from requests import Session

from anicli_ru.utils import kodik_decoder

# aniboom regular expressions (work after unescape response html page)
RE_ANIBOOM = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')

# kodik/anivod regular expressions
RE_KODIK_URL_DATA = re.compile(r'iframe.src = "//(.*?)"')
RE_KODIK_VIDEO_TYPE = re.compile(r"go/(\w+)/\d+")
RE_KODIK_VIDEO_ID = re.compile(r"go/\w+/(\d+)")
RE_KODIK_VIDEO_HASH = re.compile(r"go/\w+/\d+/(.*?)/\d+p\?")

# random anime
RE_RANDOM_ANIME_TITLE = re.compile(r"data-video-player-title>.* «(.*?)»")


class ListObj(UserList):
    """Modified list object"""

    def print_enumerate(self, *args):
        """print elements with getattr names arg or default invoke __str__ method
        """

        if len(self) > 0:
            if args:
                for i, obj in enumerate(self, 1):
                    print(f"[{i}]", *(getattr(obj, arg) for arg in args))
            else:
                for i, obj in enumerate(self, 1):
                    print(f"[{i}]", obj)
        else:
            print("Results not founded!")

    def choose(self, index: int):
        if len(self) >= index > 0:
            return self[index - 1]
        return


class BaseObj:
    """base object for responses"""
    REGEX: dict  # {"attr_name": re.compile(<regular expression>)}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = int(v) if v.isdigit() else unescape(str(v))
            setattr(self, k, v)

    @classmethod
    def parse(cls, html: str) -> ListObj:
        """class object factory"""
        l_objects = ListObj()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}
        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            l_objects.append(cls(**dict((k, v) for k, v in attrs)))
        return l_objects


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

    def info(self):
        with Anime() as a:
            return a.anime_result_info(result=self)


class AnimeInfo(BaseObj):
    """Extended Info object for AnimeResult"""
    REGEX = {
        "title": re.compile(r'data-video-player-title>.* «(.*?)»'),
        "thumbnail": re.compile(r'content="(https://animego\.org/media/cache.*?)" />'),
        "raw_description": re.compile(r'<div data-readmore="content">\s+(.*?)\s+</div>'),
        "type": re.compile(r'Тип</dt><dd class="col-6 col-sm-8 mb-1">(.*?)</dd>'),
        "_episodes": re.compile(r'Эпизоды</dt><dd class="col-6 col-sm-8 mb-1">(.*?)</dd>'),
        "genres": re.compile(r'href="https://animego\.org/anime/genre/\w+" title="(.*?)"'),
        "source": re.compile(r'Первоисточник</dt><dd class="col-6 col-sm-8 mb-1">(.*?)</dd>'),
        "release": re.compile(r'Выпуск</dt><dd class="col-6 col-sm-8 mb-1"><span data-label=".*?"><span>(.*?)</span>'),
        "studio": re.compile(r'<a href="https://animego.org/anime/studio/.*?" title="(.*?)"'),
        "rating": re.compile(r'<span class="rating-value">(.*?)</span>'),
        "status": re.compile(r'<a href="https://animego\.org/anime/status/.*?" title="(.*?)">')
    }

    title: str
    type: str
    thumbnail: str
    raw_description: str
    _episodes: str
    genres: list
    source: str
    release: str
    studio: str
    rating: str
    status: str

    @property
    def description(self):
        return re.sub("<.*?>", "", self.raw_description)

    @property
    def episodes(self):
        return re.sub("<.*?>", "", self._episodes)

    def __str__(self):
        return f"""{self.title} rating: {self.rating}
{self.status}
{self.episodes}
{self.type}
{self.description}
{self.genres}
{self.source}
{self.release}
{self.studio}
        """


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

    def info(self):
        with Anime() as a:
            return a.anime_result_info(result=self)

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
    SUPPORTED_PLAYERS = ("aniboom", "sibnet", "kodik", "anivod")
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

    def is_supported(self):
        """True if player is supported"""
        return any([_ for _ in self.SUPPORTED_PLAYERS if _ in self.url])

    @staticmethod
    def _player_prettify(player: str):
        return "https:" + unescape(player)

    def get_video(self):
        with Anime() as a:
            return a.get_video(self)

    def __str__(self):
        u = self._player.replace("//", "").split(".", 1)[0]
        return f"{self.dub_name} ({u})"


class Anime:
    """Anime class parser

    :example:
    >>> a = Anime()
    >>> results = a.search("school")
    >>> results.print_enumerate()
    >>> episodes = results[0].episodes()
    """
    BASE_URL = "https://animego.org"

    # mobile user-agent can sometimes gives a chance to bypass the anime title ban
    USER_AGENT = {"user-agent":
                      "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
                  "x-requested-with": "XMLHttpRequest"}

    def __init__(self, session: Session = None):
        """

        :param session: requests Session object with your configuration
        """
        if session:
            self.session = session
            self.session.headers.update({"x-requested-with": "XMLHttpRequest"})
        else:
            self.session = Session()
            self.session.headers.update(self.USER_AGENT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        return

    def request(self, method, url, **kwargs):
        resp = self.session.request(method, url, **kwargs)
        return resp

    def request_get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

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

    def anime_result_info(self, result: [AnimeResult, Ongoing]) -> AnimeInfo:
        """Get detailed title info for AnimeResult object"""
        resp = self.request_get(result.url).text
        return AnimeInfo.parse(resp)[0]

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

    def get_kodik_url(self, player: Player, quality: int = 720):
        """Get hls url in kodik/anivod player"""
        quality_available = (720, 480, 360, 240)
        if quality not in quality_available:
            quality = 720
        quality = str(quality)

        resp = self.request_get(player.url, headers=self.USER_AGENT.copy().update({"referer": "https://animego.org/"}))

        # prepare values for next POST request
        url_data, = re.findall(RE_KODIK_URL_DATA, resp.text)
        type_, = re.findall(RE_KODIK_VIDEO_TYPE, url_data)
        id_, = re.findall(RE_KODIK_VIDEO_ID, url_data)
        hash_, = re.findall(RE_KODIK_VIDEO_HASH, url_data)
        data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", 1)[1].split("&")}
        data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                     "ref": "https://animego.org"})
        if "kodik" in player.url:
            url = "https://kodik.info/gvi"
        elif "anivod" in player.url:
            url = "https://anivod.com/gvi"
        else:
            raise TypeError("Unknown player balancer. <get_kodik_url> method support kodik and anivod players")
        resp = self.request("POST", url, data=data,
                            headers=self.USER_AGENT.copy().update({"referer": f"https://{url_data}",
                                                                   "orgign": url.replace("/gvi", ""),
                                                                   "accept":
                                                                       "application/json, text/javascript, */*; q=0.01"
                                                                   })
                            ).json()["links"]

        if resp.get(quality):
            # 720 key return 480p video, but replace value work :O
            return kodik_decoder(resp[quality][0]["src"]).replace("480.mp4", "720.mp4") \
                if quality == "720" else kodik_decoder(resp[quality][0]["src"])
        else:
            for q in quality_available:
                if resp.get(str(q)):
                    return kodik_decoder(resp[str(q)][0]["src"])

    def get_aniboom_url(self, player: Player) -> str:
        """get aniboom video"""
        # fix 28 11 2021 request
        r = self.request_get(
            player.url,
            headers={
                "referer": "https://animego.org/",
                "user-agent":
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.114 "
                    "Safari/537.36"})

        r = unescape(r.text)
        url = re.findall(RE_ANIBOOM, r)[0].replace("\\", "")
        return url

    def get_video(self, player: Player):
        """Return direct video url

        :param Player player: player object
        :return: direct video url
        """
        if player.is_supported():
            if "sibnet" in player.url:
                return player.url
            elif "aniboom" in player.url:
                url = self.get_aniboom_url(player)
                return url
            elif "kodik" or "anivod" in player.url:
                url = self.get_kodik_url(player)
                return url
        else:
            # catch anything players for add in script
            print("Warning!", player.url, "is not supported!")
            return

    def random(self) -> [ListObj[AnimeResult], None]:
        """return random title or None, if fail get title"""
        resp = self.request_get(self.BASE_URL + "/anime/random")
        anime = AnimeResult.parse(resp.text)
        # need create new object
        if len(anime) > 0:
            anime[0].url = resp.url
            anime[0].title, = re.findall(RE_RANDOM_ANIME_TITLE, resp.text)
            return anime

        return


if __name__ == '__main__':
    a = Anime()
    # r = a.search("lain")[0]
    r = a.ongoing()[0]
    print(r.info())
