#!/usr/bin/python3
import re
from os import system
from os import name as sys_name
from html import unescape
import argparse
from base64 import b64decode

from requests import Session
from typing import Union

__all__ = (
    "Anime", "BaseObj"
)

# mobile user-agent can sometimes gives a chance to bypass the anime title ban
USER_AGENT = {"user-agent":
                  "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, "
                  "like Gecko) Chrome/94.0.4606.114 Mobile Safari/537.36",
              "x-requested-with": "XMLHttpRequest"}

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--proxy", dest="PROXY", type=str, default="", help="add proxy")
parser.add_argument("-v", "--videoplayer", dest="PLAYER", type=str, default="mpv", help="edit videoplayer. default mpv")
parser.add_argument("-hc", "--headers-command", dest="OS_HEADERS_COMMAND", type=str, default="http-header-fields",
                    help="edit headers argument name. default http-header-fields")

args = parser.parse_args()
PROXY = args.PROXY
PLAYER = args.PLAYER
OS_HEADERS_COMMAND = args.OS_HEADERS_COMMAND


class ListObj(list):
    """Modified list object"""

    def print_enumerate(self, *args):
        """print elements with getattr names arg or default invoke __str__ method

        :example:
        >>> a = Anime()
        >>> result = a.search("school")
        >>> result.print_enumerate("title")
        """

        if len(self) > 0:
            if args:
                for i, _ in enumerate(self, 1):
                    print(f"[{i}] {' '.join([_.__getattribute__(arg) for arg in args])}")
            else:
                for i, _ in enumerate(self, 1):
                    print(f"[{i}] {_}")
        else:
            print("Results not founded!")

    def choose(self, index: int):
        if len(self) >= index > 0:
            return self[index - 1]
        return


class BaseObj(object):
    """base superclass object"""
    REGEX: dict  # {"attr_name": re.compile(<regular expression>)}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = int(v) if v.isdigit() else unescape(str(v))
            self.__setattr__(k, v)

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


class Ongoing(BaseObj):
    """
    title: str - title name

    num: str - episode number

    dub: str - dubbing name

    url: str - url
    """
    REGEX = {
        "url": re.compile(r'onclick="location\.href=\'(.*?)\'"'),
        "title": re.compile(r'600">(.*?)</span></span></div><div class="ml-3 text-right">'),
        "num":
            re.compile(r'<div class="font-weight-600 text-truncate">(\d+) серия</div><div class="text-gray-dark-6">'),
        "dub": re.compile('<div class="text-gray-dark-6">(\(.*?\))</div>')}

    title: str
    num: str
    dub: str
    url: str

    @classmethod
    def parse(cls, html: str) -> ListObj:
        ongoings = ListObj()
        sorted_ongs = ListObj()
        # generate dict like {attr_name: list(values)}
        results = {k: re.findall(v, html) for k, v in cls.REGEX.items()}

        for values in zip(*results.values()):
            attrs = zip(results.keys(), values)
            # generate objects like {attr_name: attr_value}
            ongoings.append(cls(**dict((k, v) for k, v in attrs)))

        # shitty sort duplicates (by title and episode num) algorithm
        # but ongoings list contains less than 100 elements guaranty
        for o in ongoings:
            if o.title in [i.title for i in sorted_ongs]:
                for o2 in sorted_ongs:
                    if o2.title == o.title and o.num == o2.num:
                        o2.dub += ", " + o.dub
                        break
                else:
                    sorted_ongs.append(o)
            else:
                sorted_ongs.append(o)
        sorted_ongs.sort(key=lambda k: k.title)  # sort by title name
        return sorted_ongs

    @property
    def id(self) -> str:
        return self.url.split("-")[-1]

    def episodes(self):
        with Anime() as a:
            return a.episodes(result=self)

    def __str__(self):
        return f"{self.title} {self.num} {self.dub}"


class Episode(BaseObj):
    """
    num: int - episode number

    name: str 0 episode name

    id: int - episode video id
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

    player str: videoplayer url
    """
    SUPPORTED_PLAYERS = ("aniboom", "sibnet", "kodik")
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
                # TODO add new players support (anivod, etc)
                if dub_id_1 == dub_id_2:
                    p._player = player
                    p.dub_name = dub_name
                    p.dub_id = dub_id_1
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

    def run(self):
        with Anime() as a:
            return a.run_hls(self)

    def __str__(self):
        u = self._player.replace("//", "").split(".", 1)[0]
        return f"{self.dub_name} ({u})"


class Anime:
    """Anime class parser

    :example:
    >>> a = Anime()
    >>> results = a.search("school")
    >>> print(results.print_enumerate())
    >>> episodes = results[0].episodes()
    """
    BASE_URL = "https://animego.org"

    def __init__(self):
        self.session = Session()
        self.session.headers.update(USER_AGENT)

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

    def episodes(self, result) -> ListObj[Episode]:
        """Get available episodes

        :param result: Ongoing or AnimeSearch object
        :return: list available episodes
        :rtype: ListObj
        """
        resp = self.request_get(self.BASE_URL + f"/anime/{result.id}/player?_allow=true").json()["content"]
        return Episode.parse(resp)

    def players(self, episode: Episode):
        """Return videoplayers urls

        :param Episode episode: choosen Episode object
        :return: list available players
        :rtype: ListObj
        """
        resp = self.request_get(self.BASE_URL + "/anime/series", params={"dubbing": 2, "provider": 24,
                                                                         "episode": episode.num,
                                                                         "id": episode.id}).json()["content"]
        players = Player.parse(resp)
        return players

    @staticmethod
    def __run_player(url, headers=None) -> None:
        if headers:
            system(f"{PLAYER} --{OS_HEADERS_COMMAND}={headers} {url}")
        else:
            system(f"{PLAYER} {url}")

    @staticmethod
    def kodik_decoder(url_encoded: str) -> str:
        """kodik player video url decoder

        :param str url_encoded: encoded url
        :return: decoded video url"""
        url_encoded = url_encoded[::-1]
        if not url_encoded.endswith("=="):
            url_encoded += "=="
        link = b64decode(url_encoded).decode()
        if not link.startswith("https"):
            link = "https:" + link
        return link

    def get_kodik_url(self, player: Player, quality: int = 720):
        """Get hls url in kodik player"""
        quality_available = (720, 480, 360, 240)
        if quality not in quality_available:
            quality = 720
        quality = str(quality)

        url_data_pattern = re.compile(r'iframe.src = "//(.*?)"')
        video_type_pattern = re.compile(r"kodik\.info/go/(\w+)/\d+")
        video_id_pattern = re.compile(r"kodik\.info/go/\w+/(\d+)")
        video_hash_pattern = re.compile(r"kodik\.info/go/\w+/\d+/(.*?)/\d+p\?")

        resp = self.request_get(player.url, headers=USER_AGENT.copy().update({"referer": "https://animego.org/"}))

        # prepare values for next POST request
        url_data, = re.findall(url_data_pattern, resp.text)
        type_, = re.findall(video_type_pattern, url_data)
        id_, = re.findall(video_id_pattern, url_data)
        hash_, = re.findall(video_hash_pattern, url_data)
        data = {value.split("=")[0]: value.split("=")[1] for value in url_data.split("?", )[1].split("&")}
        data.update({"type": type_, "hash": hash_, "id": id_, "info": {}, "bad_user": True,
                     "ref": "https://animego.org"})

        resp = self.request("POST", "https://kodik.info/gvi", data=data,
                            headers=USER_AGENT.copy().update({"referer": f"https://{url_data}",
                                                              "orgign": "https://kodik.info",
                                                              "accept": "application/json, text/javascript, */*; q=0.01"
                                                              })
                            ).json()["links"]

        if resp.get(quality):
            # 720 key return 480p video, but replace value work :O
            return self.kodik_decoder(resp[quality][0]["src"]).replace("480.mp4", "720.mp4") \
                if quality == "720" else self.kodik_decoder(resp[quality][0]["src"])
        else:
            for q in quality_available:
                if resp.get(str(q)):
                    return self.kodik_decoder(resp[str(q)][0]["src"])

    def get_aniboom_url(self, player: Player) -> str:
        """get aniboom video"""
        aniboom_pattern = re.compile(r'"hls":"{\\"src\\":\\"(.*\.m3u8)\\"')
        # user agent keys must be write title-style
        r = self.request_get(player.url, headers={"Referer": "https://animego.org/",
                                                  "User-Agent":
                                                      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                      "(KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"})
        r = unescape(r.text)
        url = re.findall(aniboom_pattern, r)[0].replace("\\", "")
        return url

    def run_hls(self, player: Player) -> bool:
        """Run hls in local videoplayer

        :param Player player: player object
        :return:
        """
        if player.is_supported():
            if "sibnet" in player.url:
                self.__run_player(player.url)
            elif "aniboom" in player.url:
                url = self.get_aniboom_url(player)
                self.__run_player(url, headers="Referer: https://aniboom.one")
            elif "kodik" in player.url:
                url = self.get_kodik_url(player)
                self.__run_player(url)
            return True

        else:
            # catch anything players for add in script
            print("Warning!", player.url, "is not supported!")
            return False

    def random(self) -> [ListObj[AnimeResult], None]:
        """return random title or None, if fail get title"""
        resp = self.request_get(self.BASE_URL + "/anime/random")
        anime = AnimeResult.parse(resp.text)
        # need create new object
        if len(anime) > 0:
            anime[0].url = resp.url
            anime[0].title = re.findall(r"<title>(.*?) смотреть онлайн — Аниме</title>", resp.text)[0]
            return anime
        return


class Menu:
    def __init__(self):
        self.__ACTIONS = {"b": ("[b]ack next step", self.back_on),
                          "c": ("[c]lear", self.cls),
                          "h": ("[h]elp", self.help),
                          "o": ("[o]ngoing print", self.ongoing),
                          "r": ("[r]andom title", self.random),
                          "q": ("[q]uit", self.exit),
                          }
        self.anime = Anime()
        self.__back_action = True

    def back_on(self):
        self.__back_action = False

    def back_off(self):
        self.__back_action = True

    @staticmethod
    def cls():
        system("cls") if sys_name == 'nt' else system("clear")

    @property
    def is_back(self):
        return self.__back_action

    def random(self):
        anime = self.anime.random()
        if anime:
            print(anime[0])
            self.choose_episode(1, anime)

    def ongoing(self):
        while self.is_back:
            ongoings = self.anime.ongoing()
            ongoings.print_enumerate()
            print("Choose anime:", 1, "-", len(ongoings))
            command = input(f"c_o [1-{len(ongoings)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                self.choose_episode(int(command), ongoings)
        self.back_off()

    def choose_dub(self, results: ListObj[Player]):
        while self.is_back:
            results.print_enumerate()
            print("Choose dub:", 1, "-", len(results))
            command = input(f"c_d [1-{len(results)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                if int(command) <= len(results):
                    print("Start playing")
                    self.anime.run_hls(results.choose(int(command)))
        self.back_off()

    def choose_episode(self, num: int, result: ListObj[Union[AnimeResult, Ongoing]]):
        episodes = self.anime.episodes(result.choose(num))
        if len(episodes) > 0:
            while self.is_back:
                episodes.print_enumerate()
                print(f"Choose episode: 1-{len(episodes)}")
                command = input(f"c_e [1-{len(episodes)}] > ")
                if not self.command_wrapper(command) and command.isdigit():
                    if int(command) <= len(episodes):
                        results = self.anime.players(episodes.choose(int(command)))
                        if len(results) > 0:
                            self.choose_dub(results)
                        else:
                            print("No available dubs")
                            return
            self.back_off()
        else:
            print("""Warning! Episodes not found :(
This anime-title maybe blocked in your country, try using a vpn/proxy and repeat operation

""")
            print()
        return

    def choose_anime(self, results: ListObj[AnimeResult]):
        while self.is_back:
            results.print_enumerate()
            print("Choose anime:", 1, "-", len(results))
            command = input(f"c_a [1-{len(results)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                self.choose_episode(int(command), results)
        self.back_off()

    def find(self, pattern):
        results = self.anime.search(pattern)
        if len(results) > 0:
            print("Found", len(results))
            self.choose_anime(results)
        else:
            print("Not found!")
            return

    def help(self):
        for k, v in self.__ACTIONS.items():
            print(k, v[0])

    def command_wrapper(self, command):
        self.cls()
        if self.__ACTIONS.get(command):
            self.__ACTIONS[command][1]()
            return True
        return False

    def main(self):
        if PROXY:
            print("Check proxy")
            try:
                self.anime.session.get("https://animego.org", proxies=dict(http=PROXY, https=PROXY),
                                       timeout=10)
            except Exception as e:
                print(e)
                print("Failed proxy connect")
                self.exit()
            self.anime.session.proxies.update(dict(http=PROXY, https=PROXY))
            print("Proxy connect success")
        while True:
            print("Input anime name or USAGE: h for get commands")
            command = input("m > ")
            if not self.command_wrapper(command):
                self.find(command)

    @classmethod
    def run(cls):
        cls().main()

    @staticmethod
    def exit():
        exit(0)


if __name__ == '__main__':
    try:
        Menu.run()
    except KeyboardInterrupt:
        print("Exit")
