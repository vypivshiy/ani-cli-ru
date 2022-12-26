from enum import auto
import subprocess

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils import (
    make_completer,
    number_validator,
    CONCATENATE_ARGS,
    on_exit_state,
    STATE_BACK,
    STATE_MAIN_LOOP
)
from anicli.config import dp


class SearchStates(BaseState):
    SEARCH = 6
    EPISODE = 7
    VIDEO = 8
    PLAY = 9


@dp.state_handler(SearchStates.PLAY,
                  on_error=on_exit_state)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    if not(sources:=dp.state_dispenser.get_cache(video)):
        sources = video.get_source()
        dp.state_dispenser.cache_object(video, sources)
    print(*[f"[{i}] {s}" for i,s in enumerate(sources)], sep="\n")
    num = prompt("~/search/episode/quality ", completer=make_completer(sources), validator=number_validator(sources))
    if STATE_BACK(num, SearchStates.VIDEO):
        return
    elif STATE_MAIN_LOOP(num):
        return
    attrs = mpv_attrs(sources[int(num)])
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(SearchStates.VIDEO)


@dp.state_handler(SearchStates.VIDEO,
                  on_error=on_exit_state)
def search_video():
    episode: animego.Episode = dp.state_dispenser["episode"]
    if not (videos:=dp.state_dispenser.get_cache(episode)):
        videos = episode.get_videos()
        dp.state_dispenser.cache_object(episode, videos)
        
    print(*[f"[{i}] {v}" for i, v in enumerate(videos)], sep="\n")
    num = prompt("~/search/episode/video ", completer=make_completer(videos), validator=number_validator(videos))
    if STATE_BACK(num, SearchStates.EPISODE):
        return
    elif STATE_MAIN_LOOP(num):
        return
    dp.state_dispenser.update({"video": videos[int(num)]})
    dp.state_dispenser.set(SearchStates.PLAY)


@dp.state_handler(SearchStates.EPISODE,
                  on_error=on_exit_state)
def search_episodes():
    result: animego.SearchResult = dp.state_dispenser["search"]
    if not (anime:=dp.state_dispenser.get_cache(result)):
        anime = result.get_anime()
        dp.state_dispenser.cache_object(result, anime)

    print(anime)
    if not (episodes:=dp.state_dispenser.get_cache(anime)):
        episodes = anime.get_episodes()
        dp.state_dispenser.cache_object(anime, episodes)

    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("~/search/episode ", completer=make_completer(episodes), validator=number_validator(episodes))
    if STATE_BACK(num, SearchStates.SEARCH):
        return
    elif STATE_MAIN_LOOP(num):
        return
    dp.state_dispenser.update({"episode": episodes[int(num)]})
    dp.state_dispenser.set(SearchStates.VIDEO)


@dp.command("search",
            args_hook=CONCATENATE_ARGS,
            state=SearchStates.SEARCH)
def search(query: str):
    """search title by query"""
    # storage query param
    dp.state_dispenser.storage_params[SearchStates.SEARCH] =  (query,)

    # cache all values for increase speed
    if not (results:=dp.state_dispenser.get_cache(query)):
        results = EXTRACTOR.search(query)
        dp.state_dispenser.cache_object(query, results)

    if len(results) > 0:
        print(*[f"[{i}] {o}" for i, o in enumerate(results)], sep="\n")
        num = prompt("~/search ", completer=make_completer(results), validator=number_validator(results))
        if STATE_BACK(num, SearchStates.SEARCH) or STATE_MAIN_LOOP(num):
            dp.state_dispenser.finish()
            return
        dp.state_dispenser.update({"search": results[int(num)]})
        dp.state_dispenser.set(SearchStates.EPISODE)
    else:
        print("Not found")
        dp.state_dispenser.finish()


@search.on_error()
def search_error(error: BaseException):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print("search, exit")
        dp.state_dispenser.finish()
        return
