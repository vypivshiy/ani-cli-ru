#!/usr/bin/python3
from __future__ import annotations
from os import system
from os import name as sys_name
import argparse
from typing import Union

from anicli_ru.utils import run_player, is_aniboom
from string import ascii_letters
from random import sample

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--proxy", dest="PROXY", type=str, default="",
                    help="Add proxy for bypass a ban")
parser.add_argument("-d", "--download", dest="DOWNLOAD", default=False, action="store_true",
                    help="Download mode. Default False. ffmpeg required")
parser.add_argument("-q", "--quality", dest="QUALITY", type=int, default=720, choices=[360, 480, 720],
                    help="default video quality. Works only kodik. Default 720")
parser.add_argument("-i", "--instant", dest="INSTANT", default=False, action="store_true",
                    help="Instant view mode. Useful if you want to watch a title without manual switching episodes")
parser.add_argument("-s", "--source", dest="SOURCE", type=int, default=1, choices=[1, 2],
                    help="Site source. 1-animego, 2-animania. Default 1 (animego)")


args = parser.parse_args()
PROXY = args.PROXY
DOWNLOAD = args.DOWNLOAD
QUALITY = args.QUALITY
INSTANT = args.INSTANT
PLAYER = "mpv"
OS_HEADERS_COMMAND = "http-header-fields"

if args.SOURCE == 1:
    from anicli_ru.api import Anime, ListObj, Player, AnimeResult, Ongoing
elif args.SOURCE == 2:
    from anicli_ru.api2 import Anime, ListObj, Player, AnimeResult, Ongoing
print("Chosen source:", Anime.BASE_URL)


class Menu:
    def __init__(self):
        self.__ACTIONS = {"b": ("[b]ack next step", self.back_on),
                          "c": ("[c]lear", self.cls),
                          "h": ("[h]elp", self.help),
                          "o": ("[o]ngoing print", self.ongoing),
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

    def command_wrapper(self, command):
        self.cls()
        if self.__ACTIONS.get(command):
            self.__ACTIONS[command][1]()
            return True
        return False

    @staticmethod
    def exit():
        exit(0)

    def ongoing(self):
        while self.is_back:
            ongoings = self.anime.ongoing()
            if len(ongoings) > 0:
                ongoings.print_enumerate()
                print("Choose anime:", 1, "-", len(ongoings))
                command = input(f"c_o [1-{len(ongoings)}] > ")
                if not self.command_wrapper(command) and command.isdigit():
                    self.choose_episode(ongoings[int(command)-1])
            else:
                print("Cannot grub ongoings")
                return
        self.back_off()

    def _run_video(self, player: Player):
        url = self.anime.get_video(player.url, QUALITY)
        if is_aniboom(url):
            if DOWNLOAD:
                self._download(f'ffmpeg -y -headers "Referer: https://aniboom.one" -i "{url}" "{"".join(sample(ascii_letters, 12))}.mp4"')
            else:
                command_ = {OS_HEADERS_COMMAND: "Referer: https://aniboom.one"}
                run_player(url, **command_)
        else:
            if DOWNLOAD:
                self._download(f'ffmpeg -y -i "{url}" "{"".join(sample(ascii_letters, 12))}.mp4"')
            else:
                run_player(url)

    def _download(self, command: str):
        system(command)

    def choose_dub(self, results: ListObj[Player]):
        while self.is_back:
            results.print_enumerate()
            print("Choose dub:", 1, "-", len(results))
            command = input(f"c_d [1-{len(results)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                if int(command) <= len(results):
                    print("Start playing")
                    if INSTANT:
                        for player in results[int(command)-1:]:
                            self._run_video(player)

                    else:
                        self._run_video(results[int(command)-1])
        self.back_off()

    def choose_episode(self, result: Union[AnimeResult, Ongoing]):
        episodes = result.episodes()
        if len(episodes) > 0:
            while self.is_back:
                episodes.print_enumerate()
                print(f"Choose episode: 1-{len(episodes)}")
                command = input(f"c_e [1-{len(episodes)}] > ")
                if not self.command_wrapper(command) and command.isdigit():
                    if int(command) <= len(episodes):
                        results = episodes[int(command)-1].player()
                        if len(results) > 0:
                            self.choose_dub(results)
                        else:
                            print("No available dubs")
                            return
            self.back_off()
        else:
            print("Warning! Episodes not found :(\nThis anime-title maybe blocked in your country, try using a vpn/proxy or use -s argument and repeat operation")
        return

    def choose_anime(self, results: ListObj[AnimeResult]):
        while self.is_back:
            results.print_enumerate()
            print("Choose anime:", 1, "-", len(results))
            command = input(f"c_a [1-{len(results)}] > ")
            if not self.command_wrapper(command) and command.isdigit():
                if 0 < int(command) <= len(results):
                    self.choose_episode(results[int(command)-1])
                return
        self.back_off()

    def find(self, pattern):
        results = self.anime.search(pattern)
        if len(results) > 0:
            print("Found", len(results))
            self.choose_anime(results)
        else:
            print("Not found!")
            return

    def main(self):
        if PROXY:
            self.proxy()
        while True:
            print("Input anime name or USAGE: h for get commands")
            command = input("m > ")
            if not self.command_wrapper(command):
                self.find(command)

    def help(self):
        for k, v in self.__ACTIONS.items():
            print(k, v[0])

    def proxy(self):
        print("Check proxy")
        try:
            self.anime.session.get(self.anime.BASE_URL, proxies=dict(http=PROXY, https=PROXY),
                                   timeout=10)
        except Exception:
            print("Failed proxy connect")
            self.exit()
        self.anime.session.proxies.update(dict(http=PROXY, https=PROXY))
        print("Proxy connect success")

    @classmethod
    def run(cls):
        cls().main()


if __name__ == '__main__':
    try:
        Menu.run()
    except KeyboardInterrupt:
        print("Exit")
