#!/usr/bin/python3
from os import system
from os import name as sys_name
import argparse
from typing import Union

from anicli_ru import Anime
from anicli_ru.api import ListObj, Player, AnimeResult, Ongoing
from anicli_ru.utils import run_player, is_aniboom


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--proxy", dest="PROXY", type=str, default="", help="add proxy")
parser.add_argument("-v", "--videoplayer", dest="PLAYER", type=str, default="mpv", help="edit videoplayer. default mpv")
parser.add_argument("-hc", "--headers-command", dest="OS_HEADERS_COMMAND", type=str, default="http-header-fields",
                    help="edit headers argument name. default http-header-fields")
parser.add_argument("-i", "--instant", dest="INSTANT", action="store_true", default=False,
                    help="Set instant view without change episodes")

args = parser.parse_args()
PROXY = args.PROXY
PLAYER = args.PLAYER
OS_HEADERS_COMMAND = args.OS_HEADERS_COMMAND
INSTANT = args.INSTANT


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
        self.__instant_dub = None
        self.__instant_player = None

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
                    url = self.anime.get_video(results.choose(int(command)))
                    if is_aniboom(url):
                        command_ = {OS_HEADERS_COMMAND: "Referer: https://aniboom.one"}
                        run_player(url, **command_)
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
