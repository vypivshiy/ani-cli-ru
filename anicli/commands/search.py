from enum import auto
import subprocess

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils import make_completer, number_validator, CONCATENATE_ARGS
from anicli.config import dp


class SearchStates(BaseState):
    BACK = 5
    SEARCH = 6
    EPISODE = 7
    VIDEO = 8
    PLAY = 9


@dp.state_handler(SearchStates.PLAY)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    sources = video.get_source()
    print(*[f"[{i}] {s}" for i,s in enumerate(sources)], sep="\n")
    num = prompt("[QUALITY] > ", completer=make_completer(sources), validator=number_validator(sources))
    if num == "..":
        dp.state_dispenser.set(SearchStates.VIDEO)
        return
    source = sources[int(num)]
    attrs = mpv_attrs(source)
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(SearchStates.VIDEO)


@dp.state_handler(SearchStates.VIDEO)
def search_video():
    episode: animego.Episode = dp.state_dispenser["episode"]
    videos = episode.get_videos()
    print(*[f"[{i}] {v}" for i, v in enumerate(videos)], sep="\n")
    num = prompt("[VIDEO] > ", completer=make_completer(videos), validator=number_validator(videos))
    if num == "..":
        dp.state_dispenser.set(SearchStates.EPISODE)
        return
    video = videos[int(num)]
    dp.state_dispenser.update_data({"video": video})
    dp.state_dispenser.set(SearchStates.PLAY)


@dp.state_handler(SearchStates.EPISODE)
def search_episodes():
    result = dp.state_dispenser["search"]
    anime = result.get_anime()
    print(anime)
    episodes = anime.get_episodes()
    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("[EPISODE] > ", completer=make_completer(episodes), validator=number_validator(episodes))
    if num == "..":
        dp.state_dispenser.set(SearchStates.SEARCH)
        return
    episode = episodes[int(num)]
    dp.state_dispenser.update_data({"episode": episode})
    dp.state_dispenser.set(SearchStates.VIDEO)


@dp.command("search", args_hook=CONCATENATE_ARGS)
@dp.state_handler(SearchStates.SEARCH)
def search(query: str):
    """search title by query"""
    results = EXTRACTOR.search(query)
    if len(results) > 0:
        print(*[f"[{i}] {o}" for i, o in enumerate(results)], sep="\n")
        num = prompt("[SEARCH] > ", completer=make_completer(results), validator=number_validator(results))
        if num == "..":
            dp.state_dispenser.finish()
            return
        dp.state_dispenser.update_data({"search": results[int(num)]})
        dp.state_dispenser.set(SearchStates.EPISODE)
    else:
        print("Not found")
        dp.state_dispenser.finish()


@search.on_error()
def search_error(error: BaseException):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print("search, exit")
        return
