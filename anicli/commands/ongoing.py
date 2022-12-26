import subprocess

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils.states import STATE_BACK, STATE_MAIN_LOOP, on_exit_state
from anicli.commands.utils.validators import make_completer, number_validator, number_slice_validator, slice_digit
from anicli.config import dp


class OngoingStates(BaseState):
    ONGOING = 0
    EPISODE = 1
    VIDEO = 2
    PLAY = 3
    SLICE_PLAY = 4


@dp.state_handler(OngoingStates.SLICE_PLAY, on_error=on_exit_state)
def slice_play():
    video_, source_ = None, None
    episodes: list[animego.Episode] = dp.state_dispenser["episodes"]
    for episode in episodes:
        videos = episode.get_videos()
        if not video_:
            num = prompt("~/ongoing/slice_play/video ",
                         completer=make_completer(videos),
                         validator=number_validator(videos))
            if STATE_BACK(num, OngoingStates.EPISODE):
                return
            elif STATE_MAIN_LOOP(num):
                return
            video_ = videos[int(num)]
        if not source_:
            sources = video_.get_source()
            num = prompt("~/ongoing/slice_play/quality ",
                         completer=make_completer(sources),
                         validator=number_validator(sources))
            if STATE_BACK(num, OngoingStates.EPISODE):
                return
            elif STATE_MAIN_LOOP(num):
                return
            source_ = sources[int(num)]
        for video in videos:
            # TODO make checks more reliable, like hash comparison...
            if video.dict()["dub_id"] == video_.dict()["dub_id"] and video.dict()["name"] == video_.dict()["name"]:
                for source in video.get_source():
                    if source_.quality == source.quality and source.type == source_.type:
                        attrs = mpv_attrs(source)
                        subprocess.run(" ".join(attrs), shell=True)
                        break
                break
    dp.state_dispenser.set(OngoingStates.EPISODE)


@dp.state_handler(OngoingStates.PLAY,
                  on_error=on_exit_state)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    sources = dp.state_dispenser.from_cache(video, video.get_source)
    print(*[f"[{i}] {s}" for i,s in enumerate(sources)], sep="\n")
    num = prompt("~/ongoing/episode/video/quality ",
                 completer=make_completer(sources),
                 validator=number_validator(sources))
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
    videos = dp.state_dispenser.from_cache(episode, episode.get_videos)
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
    anime = dp.state_dispenser.from_cache(result, result.get_anime)
    print(anime)
    episodes = dp.state_dispenser.from_cache(anime, anime.get_episodes)
    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("~/ongoing/episode ", completer=make_completer(episodes), validator=number_slice_validator(episodes))
    if STATE_BACK(num, OngoingStates.ONGOING):
        return
    elif STATE_MAIN_LOOP(num):
        return
    elif slice_ := slice_digit(num):
        dp.state_dispenser.update({"episodes": episodes[slice_]})
        dp.state_dispenser.set(OngoingStates.SLICE_PLAY)
        return
    episode = episodes[int(num)]
    dp.state_dispenser.update({"episode": episode})
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.command("ongoing", state=OngoingStates.ONGOING)
def ongoing():
    """search last published titles"""
    ongoings = dp.state_dispenser.from_cache("ongoings", EXTRACTOR.ongoing)

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
