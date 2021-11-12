#!/usr/bin/python3
import re
from os import system
from os import name as sys_name
from html import unescape
import argparse


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
                    print(f"[{i}] {_.__str__()}")
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
        for values in list(zip(*results.values())):
            s = list(zip(results.keys(), values))
            # generate objects like {attr_name: attr_value}
            l_objects.append(cls(**dict((k, v) for k, v in s)))
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

    dub_name ont: dubbing name

    player str: videoplayer url
    """
    REGEX = {
        "dub_id":
            re.compile(r'data-dubbing="(\d+)"><span class="video-player-toggle-item-name text-underline-hover">\s+.*'),
        "dub_name":
            re.compile(r'data-dubbing="\d+"><span class="video-player-toggle-item-name text-underline-hover">\s+(.*)'),
        "player_urls_raw": re.compile(r'data-provider="\d+"\s+data-provide-dubbing="(\d+).*\s+data-player="(.*?)"')
    }
    dub_id: int
    dub_name: str
    player_urls_raw: tuple
    _player: str = ""

    @property
    def url(self) -> str:
        if not self._player.startswith("http"):
            self._player = self.player_urls_raw[1]
            self._player = self._player_prettify(self._player)
            return self._player
        return self._player

    def is_unsupported(self):
        return not ("kodik" in self.url or "anivod" in self.url)

    @staticmethod
    def _player_prettify(player: str):
        return "https:" + player.replace("amp;", "").replace("\\", "")

    def run(self):
        with Anime() as a:
            return a.run_hls(self)

    def __str__(self):
        return f"{self.dub_name}"


class Anime:
    """Anime class parser

    :example:
    >>> a = Anime()
    >>> results = a.search("school")
    >>> print(results.print_enumerate())
    >>> episodes = results[0].episodes()
    """
    BASE_URL = "https://animego.org"
    ANIBOOM_PATTERN = re.compile(r"hls:\{src:(.*\.m3u8)")

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
        ongs = ListObj(Ongoing.parse(resp))
        sorted_ongs = ListObj()
        # shitty sort duplicates (by title and episode num) algorithm
        for o in ongs:
            if o.title in [i.title for i in sorted_ongs]:
                for o2 in sorted_ongs:
                    if o2.title == o.title and o.num == o2.num:
                        o2.dub += ", " + o.dub
            else:
                sorted_ongs.append(o)
        sorted_ongs.sort(key=lambda k: k.title)  # sort by title name
        return sorted_ongs

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
        players = ListObj([p for p in players if p.is_unsupported()])
        return players

    @staticmethod
    def __run_player(url, headers=None) -> None:
        if headers:
            system(f"{PLAYER} --{OS_HEADERS_COMMAND}={headers} {url}")
        else:
            system(f"{PLAYER} {url}")

    def run_hls(self, player: Player) -> bool:
        """Run hls in local videoplayer

        :param Player player: player object
        :return:
        """
        if not player.is_unsupported():
            return False
        # hardcoded, because only 2 players are guaranteed to work
        if "sibnet" in player.url:
            self.__run_player(player.url)

        elif "aniboom" in player.url:
            # user agent must rows must be write title-style
            r = self.request_get(player.url,
                                 headers={"Referer": "https://animego.org/",
                                          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                        "(KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"})
            r = r.text.replace("&quot;", "").replace("\\", "")
            url = re.findall(self.ANIBOOM_PATTERN, r)[0]
            self.__run_player(url, headers="Referer: https://aniboom.one")
        return True

    def random(self) -> [ListObj[AnimeResult],  None]:
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