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

from anicli.commands.options import mpv_attrs
from anicli.commands.tools import CONCATENATE_ARGS, print_enumerate, SingletonStorage
from anicli.commands.validators import (
    enumerate_completer,
    number_slice_validator,
    number_validator,
    slice_digit,
)

from anicli.commands.widgets.pager import spawn_pager
from anicli.config import dp
from anicli.core import BaseState


class SearchStates(BaseState):
    """states actions commands"""
    SEARCH = 10
    EPISODE = 11
    VIDEO = 12
    PLAY = 13
    SLICE_PLAY = 14
    INFO = 15


@dp.on_state_handler(SearchStates.INFO)
def info_pager():
    """spawn pager with all anime metadata"""
    metadata: dict = dp.state_dispenser["meta"]
    prev_state: BaseState = dp.state_dispenser["prev_state"]
    spawn_pager(metadata)
    dp.state_dispenser.set(prev_state)


@dp.on_state_handler(SearchStates.SLICE_PLAY)
def slice_play():
    """Play all slice of episodes"""
    video_, source_ = None, None
    episodes: list = dp.state_dispenser["episodes"]
    for episode in episodes:
        videos = episode.get_videos()
        # choose video dub
        if not video_:
            num = prompt(
                "~/search/slice_play/video ",
                completer=enumerate_completer(videos, whitelist_commands=BUILDIN_COMMANDS),
                validator=number_validator(videos, whitelist_commands=set(BUILDIN_COMMANDS.keys())),
            )
            if ON_STATE_BACK(num, SearchStates.EPISODE):
                return
            elif ON_STATE_MAIN(num):
                return
            video_ = videos[int(num)]
        # choose source like quality, video hosting
        if not source_:
            sources = video_.get_source()
            num = prompt(
                "~/search/slice_play/quality ",
                completer=enumerate_completer(sources, whitelist_commands=BUILDIN_COMMANDS),
                validator=number_validator(sources, whitelist_commands=set(BUILDIN_COMMANDS.keys())))
            if ON_STATE_BACK(num, SearchStates.EPISODE):
                return
            elif ON_STATE_MAIN(num):
                return
            source_ = sources[int(num)]

        # compare previous chooses and play all slice of episodes
        for video in videos:
            # TODO make checks more reliable, like hash comparison...
            if (video.dict()["dub_id"] == video_.dict()["dub_id"]
                and video.dict()["name"] == video_.dict()["name"]):
                for source in video.get_source():
                    if (source_.quality == source.quality
                        and source.type == source_.type):
                        attrs = mpv_attrs(source)
                        subprocess.run(" ".join(attrs), shell=True)
                        break
                break
    # return to `SearchStates.EPISODE` state
    dp.state_dispenser.set(SearchStates.EPISODE)


@dp.on_state_handler(SearchStates.PLAY, on_error=ON_ERROR_STATE)
def play():
    video = dp.state_dispenser["video"]
    if not(sources := dp.state_dispenser.cache.get(video)):
        dp.state_dispenser.cache[video] = video.get_source()
        sources = dp.state_dispenser.cache[video]

    print_enumerate(sources)
    num = prompt(
        "~/search/episode/quality ",
        completer=enumerate_completer(sources, whitelist_commands=BUILDIN_COMMANDS),
        validator=number_validator(sources, whitelist_commands=set(BUILDIN_COMMANDS.keys())))
    if ON_STATE_BACK(num, SearchStates.VIDEO):
        return
    elif ON_STATE_MAIN(num):
        return
    attrs = mpv_attrs(sources[int(num)])
    subprocess.run(" ".join(attrs), shell=True)
    dp.state_dispenser.set(SearchStates.VIDEO)


@dp.on_state_handler(SearchStates.VIDEO, on_error=ON_ERROR_STATE)
def search_video():
    episode = dp.state_dispenser["episode"]
    if not (videos := dp.state_dispenser.cache.get(episode)):
        dp.state_dispenser.cache[episode] = episode.get_videos()
        videos = dp.state_dispenser.cache[episode]
    print_enumerate(videos)
    num = prompt(
        "~/search/episode/video ",
        completer=enumerate_completer(videos, whitelist_commands=BUILDIN_COMMANDS),
        validator=number_validator(videos, whitelist_commands=set(BUILDIN_COMMANDS.keys())
        ))
    if ON_STATE_BACK(num, SearchStates.EPISODE):
        return
    elif ON_STATE_MAIN(num):
        return
    dp.state_dispenser.update({"video": videos[int(num)]})
    dp.state_dispenser.set(SearchStates.PLAY)


@dp.on_state_handler(SearchStates.EPISODE, on_error=ON_ERROR_STATE)
def search_episodes():
    # get calculate result from state_dispenser.storage
    result = dp.state_dispenser["search"]

    # get anime, episodes and cache to state_dispenser.cache storage
    if not (anime := dp.state_dispenser.cache.get(result)):
        dp.state_dispenser.cache[result] = result.get_anime()
        anime = dp.state_dispenser.cache[result]
    if not (episodes := dp.state_dispenser.cache.get(anime)):
        dp.state_dispenser.cache[anime] = anime.get_episodes()
        episodes = dp.state_dispenser.cache[anime]

    print_enumerate(episodes)
    print("type `show` for get more title information")
    extra_commands = {}
    extra_commands.update()
    extra_commands.update(OPTIONAL_COMMANDS)

    num = prompt(
        "~/search/episode ",
        completer=enumerate_completer(episodes, whitelist_commands=extra_commands),
        validator=number_slice_validator(episodes, whitelist_commands=list(extra_commands.keys())
        ),
    )
    # check `..` output
    if ON_STATE_BACK(num, SearchStates.SEARCH):
        return
    # check `~` output
    elif ON_STATE_MAIN(num):
        return
    # check `show output` and spawn pager with all metadata
    elif ON_STATE_PAGER(num, anime.dict(), SearchStates.EPISODE, SearchStates.INFO):
        return
    elif num.isdigit():
        dp.state_dispenser.update({"episode": episodes[int(num)]})
        dp.state_dispenser.set(SearchStates.VIDEO)
        return
    # check slice output \d+-\d+ pattern. Example: 1-3, 5-9 ...
    elif slice_episodes := slice_digit(num):
        dp.state_dispenser.update({"episodes": episodes[slice_episodes]})
        dp.state_dispenser.set(SearchStates.SLICE_PLAY)
        return


@dp.on_command("search", args_hook=CONCATENATE_ARGS, state=SearchStates.SEARCH)
def search(query: str):
    """search title by query"""
    # storage query param for correct return to this state
    dp.state_dispenser.storage_params[SearchStates.SEARCH] = (query,)

    # search for titles, caching in memory to increase the speed (no need to send http request again!)
    if not (results := dp.state_dispenser.cache.get(query)):
        results = SingletonStorage().extractor.search(query)
        dp.state_dispenser.cache[query] = results

    if len(results) == 0:
        print("Not found")
        dp.state_dispenser.finish()
        return

    print_enumerate(results)  # type: ignore
    # USAGE new prompt_toolkit.prompt or prompt_toolkit.PromptSession instances!
    # if you use dp.loop.session PromptSession,
    # then this instance rewrite configuration and broke REPL application!
    num = prompt(
        "~/search ",
        completer=enumerate_completer(results, whitelist_commands=BUILDIN_COMMANDS),  # type: ignore
        validator=number_validator(results, whitelist_commands=set(BUILDIN_COMMANDS.keys())))  # type: ignore
    # check `..` and `~` inputs
    if ON_STATE_BACK(num, SearchStates.SEARCH) or ON_STATE_MAIN(num):
        dp.state_dispenser.finish()
        return
    # set chosen title, push to storage and jump to `SearchStates.EPISODE` state
    dp.state_dispenser.update({"search": results[int(num)]})
    dp.state_dispenser.set(SearchStates.EPISODE)



@search.on_error()
def search_error(error: BaseException):
    """handle KeyboardInterrupt, EOFError errors"""
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print("Search KeyboardInterrupt, exit")
        dp.state_dispenser.finish()
        return
