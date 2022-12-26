import subprocess
from functools import partial

from prompt_toolkit import prompt

from anicli.core import BaseState

from anicli.commands.options import EXTRACTOR, animego, mpv_attrs
from anicli.commands.utils.validators import make_completer, number_validator, slice_digit, number_slice_validator
from anicli.commands.utils.states import STATE_BACK, STATE_MAIN_LOOP, on_exit_state
from anicli.commands.utils.tools import CONCATENATE_ARGS

from anicli.config import dp


class SearchStates(BaseState):
    SEARCH = 10
    EPISODE = 11
    VIDEO = 12
    PLAY = 13
    SLICE_PLAY = 14


@dp.state_handler(SearchStates.SLICE_PLAY)
def slice_play():
    video_, source_ = None, None
    episodes: list[animego.Episode] = dp.state_dispenser["episodes"]
    for episode in episodes:
        videos = episode.get_videos()
        if not video_:
            num = prompt("~/search/slice_play/video ",
                         completer=make_completer(videos),
                         validator=number_validator(videos))
            if STATE_BACK(num, SearchStates.EPISODE):
                return
            elif STATE_MAIN_LOOP(num):
                return
            video_ = videos[int(num)]
        if not source_:
            sources = video_.get_source()
            num = prompt("~/search/slice_play/quality ",
                         completer=make_completer(sources),
                         validator=number_validator(sources))
            if STATE_BACK(num, SearchStates.EPISODE):
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
    dp.state_dispenser.set(SearchStates.EPISODE)


@dp.state_handler(SearchStates.PLAY,
                  on_error=on_exit_state)
def play():
    video: animego.Video = dp.state_dispenser["video"]
    sources = dp.state_dispenser.from_cache(video, video.get_source)
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
    videos = dp.state_dispenser.from_cache(episode, episode.get_videos)
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
    anime = dp.state_dispenser.from_cache(result, result.get_anime)
    print(anime)
    episodes = dp.state_dispenser.from_cache(anime, anime.get_episodes)
    print(*[f"[{i}] {o}" for i, o in enumerate(episodes)], sep="\n")
    num = prompt("~/search/episode ", completer=make_completer(episodes), validator=number_slice_validator(episodes))
    if STATE_BACK(num, SearchStates.SEARCH):
        return
    elif STATE_MAIN_LOOP(num):
        return
    elif slice_ := slice_digit(num):
        dp.state_dispenser.update({"episodes": episodes[slice_]})
        dp.state_dispenser.set(SearchStates.SLICE_PLAY)
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

    if results := dp.state_dispenser.from_cache(
        query, partial(EXTRACTOR.search, query=query)
    ):
        print(*[f"[{i}] {o}" for i, o in enumerate(results)], sep="\n")
        num = prompt("~/search ",
                     completer=make_completer(results),  # type: ignore
                     validator=number_validator(results))  # type: ignore
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
