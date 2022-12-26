import subprocess

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils import (
    make_completer,
    number_validator,
    on_exit_state,
    STATE_BACK,
    STATE_MAIN_LOOP
)
from anicli.config import dp


class OngoingStates(BaseState):
    ONGOING = 1
    EPISODE = 2
    VIDEO = 3
    PLAY = 4


@dp.state_handler(OngoingStates.PLAY,
                  on_error=on_exit_state)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    if not(sources:=dp.state_dispenser.get_cache(video)):
        sources = video.get_source()
        dp.state_dispenser.cache_object(video, sources)

    print(*[f"[{i}] {s}" for i,s in enumerate(sources)], sep="\n")
    num = prompt("~/ongoing/episode/video/quality ", completer=make_completer(sources), validator=number_validator(sources))
    if STATE_BACK(num, OngoingStates.VIDEO):
        return
    elif STATE_MAIN_LOOP(num):
        return
    source = sources[int(num)]
    attrs = mpv_attrs(source)
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.state_handler(OngoingStates.VIDEO,
                  on_error=on_exit_state)
def ongoing_video():
    episode: animego.Episode = dp.state_dispenser["episode"]
    if not (videos:=dp.state_dispenser.get_cache(episode)):
        videos = episode.get_videos()
        dp.state_dispenser.cache_object(episode, videos)

    print(*[f"[{i}] {v}" for i, v in enumerate(videos)], sep="\n")
    num = prompt("~/ongoing/episode/video ", completer=make_completer(videos), validator=number_validator(videos))
    if STATE_BACK(num, OngoingStates.EPISODE):
        return
    elif STATE_MAIN_LOOP(num):
        return
    video = videos[int(num)]
    dp.state_dispenser.update({"video": video})
    dp.state_dispenser.set(OngoingStates.PLAY)


@dp.state_handler(OngoingStates.EPISODE,
                  on_error=on_exit_state)
def ongoing_episodes():
    result: animego.Ongoing = dp.state_dispenser["result"]
    if not (anime:=dp.state_dispenser.get_cache(result)):
        anime = result.get_anime()
        dp.state_dispenser.cache_object(result, anime)

    print(anime)
    if not (episodes:=dp.state_dispenser.get_cache(anime)):
        episodes = anime.get_episodes()
        dp.state_dispenser.cache_object(anime, episodes)

    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("~/ongoing/episode ", completer=make_completer(episodes), validator=number_validator(episodes))
    if STATE_BACK(num, OngoingStates.ONGOING):
        return
    elif STATE_MAIN_LOOP(num):
        return
    episode = episodes[int(num)]
    dp.state_dispenser.update({"episode": episode})
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.command("ongoing", state=OngoingStates.ONGOING)
def ongoing():
    """search last published titles"""
    if not (ongoings:=dp.state_dispenser.get_cache("ongoings")):
        ongoings = EXTRACTOR.ongoing()
        dp.state_dispenser.cache_object("ongoings", ongoings)

    if len(ongoings) > 0:
        print(*[f"[{i}] {o}" for i, o in enumerate(ongoings)], sep="\n")
        num = prompt("~/ongoing ", completer=make_completer(ongoings), validator=number_validator(ongoings))
        if STATE_BACK(num, OngoingStates.ONGOING) or STATE_MAIN_LOOP(num):
            dp.state_dispenser.finish()
            return
        dp.state_dispenser.update({"result": ongoings[int(num)]})
        dp.state_dispenser.set(OngoingStates.EPISODE)
    else:
        print("Not found")
        dp.state_dispenser.finish()


@ongoing.on_error()
def ong_error(error: BaseException):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        dp.state_dispenser.finish()
        print("ongoing, exit")
        return
