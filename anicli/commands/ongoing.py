import subprocess

from prompt_toolkit import prompt

from anicli.commands.buildin import (
    BUILDIN_COMMANDS,
    ON_ERROR_STATE,
    ON_STATE_BACK,
    ON_STATE_MAIN,
    ON_STATE_PAGER,
    OPTIONAL_COMMANDS,
)
from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.tools import print_enumerate
from anicli.commands.validators import (
    enumerate_completer,
    number_slice_validator,
    number_validator,
    slice_digit,
)
from anicli.commands.widgets.pager import spawn_pager
from anicli.config import dp
from anicli.core import BaseState


class OngoingStates(BaseState):
    ONGOING = 0
    EPISODE = 1
    VIDEO = 2
    PLAY = 3
    SLICE_PLAY = 4
    INFO = 5


@dp.on_state_handler(OngoingStates.INFO)
def info_pager():
    metadata: dict = dp.state_dispenser["meta"]
    prev_state: BaseState = dp.state_dispenser["prev_state"]
    spawn_pager(metadata)
    dp.state_dispenser.set(prev_state)


@dp.on_state_handler(OngoingStates.SLICE_PLAY, on_error=ON_ERROR_STATE)
def slice_play():
    video_, source_ = None, None
    episodes: list[animego.Episode] = dp.state_dispenser["episodes"]
    for episode in episodes:
        videos = episode.get_videos()
        if not video_:
            num = prompt(
                "~/ongoing/slice_play/video ",
                completer=enumerate_completer(
                    videos, whitelist_commands=BUILDIN_COMMANDS
                ),
                validator=number_validator(
                    videos, whitelist_commands=set(BUILDIN_COMMANDS.keys())
                ),
            )
            if ON_STATE_BACK(num, OngoingStates.EPISODE):
                return
            elif ON_STATE_MAIN(num):
                return
            video_ = videos[int(num)]
        if not source_:
            sources = video_.get_source()
            num = prompt(
                "~/ongoing/slice_play/quality ",
                completer=enumerate_completer(
                    sources, whitelist_commands=BUILDIN_COMMANDS
                ),
                validator=number_validator(
                    sources, whitelist_commands=set(BUILDIN_COMMANDS.keys())
                ),
            )
            if ON_STATE_BACK(num, OngoingStates.EPISODE):
                return
            elif ON_STATE_MAIN(num):
                return
            source_ = sources[int(num)]
        for video in videos:
            # TODO make checks more reliable, like hash comparison...
            if (
                video.dict()["dub_id"] == video_.dict()["dub_id"]
                and video.dict()["name"] == video_.dict()["name"]
            ):
                for source in video.get_source():
                    if (
                        source_.quality == source.quality
                        and source.type == source_.type
                    ):
                        attrs = mpv_attrs(source)
                        subprocess.run(" ".join(attrs), shell=True)
                        break
                break
    dp.state_dispenser.set(OngoingStates.EPISODE)


@dp.on_state_handler(OngoingStates.PLAY, on_error=ON_ERROR_STATE)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    sources = dp.state_dispenser.get_from_cache(video, video.get_source)
    print_enumerate(sources)
    num = prompt(
        "~/ongoing/episode/video/quality ",
        completer=enumerate_completer(sources, whitelist_commands=BUILDIN_COMMANDS),
        validator=number_validator(
            sources, whitelist_commands=set(BUILDIN_COMMANDS.keys())
        ),
    )
    if ON_STATE_BACK(num, OngoingStates.VIDEO):
        return
    elif ON_STATE_MAIN(num):
        return
    source = sources[int(num)]
    attrs = mpv_attrs(source)
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.on_state_handler(OngoingStates.VIDEO, on_error=ON_ERROR_STATE)
def ongoing_video():
    episode: animego.Episode = dp.state_dispenser["episode"]
    videos = dp.state_dispenser.get_from_cache(episode, episode.get_videos)
    print_enumerate(videos)
    num = prompt(
        "~/ongoing/episode/video ",
        completer=enumerate_completer(videos, whitelist_commands=BUILDIN_COMMANDS),
        validator=number_validator(
            videos, whitelist_commands=set(BUILDIN_COMMANDS.keys())
        ),
    )
    if ON_STATE_BACK(num, OngoingStates.EPISODE):
        return
    elif ON_STATE_MAIN(num):
        return
    video = videos[int(num)]
    dp.state_dispenser.update({"video": video})
    dp.state_dispenser.set(OngoingStates.PLAY)


@dp.on_state_handler(OngoingStates.EPISODE, on_error=ON_ERROR_STATE)
def ongoing_episodes():
    result: animego.Ongoing = dp.state_dispenser["result"]
    anime = dp.state_dispenser.get_from_cache(result, result.get_anime)
    episodes = dp.state_dispenser.get_from_cache(anime, anime.get_episodes)
    print_enumerate(episodes)
    extra_commands = {}
    extra_commands.update(BUILDIN_COMMANDS)
    extra_commands.update(OPTIONAL_COMMANDS)

    print("type `show` for get more title information")
    num = prompt(
        "~/ongoing/episode ",
        completer=enumerate_completer(episodes, whitelist_commands=extra_commands),
        validator=number_slice_validator(
            episodes, whitelist_commands=set(extra_commands.keys())
        ),
    )
    if ON_STATE_BACK(num, OngoingStates.ONGOING):
        return
    elif ON_STATE_MAIN(num):
        return
    elif ON_STATE_PAGER(num, anime.dict(), OngoingStates.EPISODE, OngoingStates.INFO):
        return
    elif slice_episodes := slice_digit(num):
        dp.state_dispenser.update({"episodes": episodes[slice_episodes]})
        dp.state_dispenser.set(OngoingStates.SLICE_PLAY)
        return
    episode = episodes[int(num)]
    dp.state_dispenser.update({"episode": episode})
    dp.state_dispenser.set(OngoingStates.VIDEO)


@dp.on_command("ongoing", state=OngoingStates.ONGOING)
def ongoing():
    """search last published titles"""
    ongoings = dp.state_dispenser.get_from_cache("ongoings", EXTRACTOR.ongoing)

    if len(ongoings) > 0:
        print_enumerate(ongoings)
        num = prompt(
            "~/ongoing ",
            completer=enumerate_completer(
                ongoings, whitelist_commands=BUILDIN_COMMANDS
            ),
            validator=number_validator(
                ongoings, whitelist_commands=set(BUILDIN_COMMANDS.keys())
            ),
        )
        if ON_STATE_BACK(num, OngoingStates.ONGOING) or ON_STATE_MAIN(num):
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
