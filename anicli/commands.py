import subprocess
from functools import partial
from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.validation import Validator

from anicli_api.base import BaseAnimeInfo, MetaVideo
from anicli_api.extractors import animego
from anicli.config import app


EXTRACTOR = animego.Extractor()
PLAYER = "mpv"


def make_validator(function: Callable[..., bool], *args, **keywords) -> Validator:
    function = partial(function, *args, **keywords)
    return Validator.from_callable(function)


def _number_func(digit: str, max_len: int):
    return digit.isdigit() and 0 <= int(digit) < max_len


def number_validator(max_len: int) -> Validator:
    func = partial(_number_func, max_len=max_len)
    return Validator.from_callable(func, error_message=f"Should be integer and (0<=n<{max_len})")


def get_video(session: PromptSession, anime_info: animego.AnimeInfo):
    episodes = anime_info.get_episodes()
    print(*[f"{i} - {e.num} {e.name}" for i, e in enumerate(episodes)], sep="\n")
    num = int(session.prompt("[EPISODE] > ", validator=number_validator(len(episodes))))
    episode = episodes[num]
    videos = episode.get_videos()
    print("choose video host:")
    print(*[f"{i} {v.url}" for i, v in enumerate(videos)], sep="\n")
    num = int(session.prompt("[VIDEO] > ", validator=number_validator(len(videos))))
    sources: list[MetaVideo] = videos[num].get_source()
    print("Quality:")
    # print(*[f"{i} {v}" for i, v in sources])
    num = int(session.prompt("[QUALITY] > ", validator=number_validator(len(sources))))
    source = sources[num]
    print(source.url)
    if source.extra_headers:
        print("TODO")
        return
    else:
        subprocess.run([PLAYER, source.url])


def _is_not_empty_query(*args: str):
    if not args:
        print("input query")
        return False
    return True


@app.command(["search", "find"], "search anime titles by query",
             args_hook=lambda *args: (" ".join(list(args)),),
             rule=_is_not_empty_query)
def search(query: str):
    results = EXTRACTOR.search(query)
    if len(results) > 0:
        print(*[f"{i} {r.name}" for i, r in enumerate(results)], sep="\n")
        print("choose title")
        session = app.new_prompt_session()
        num = int(session.prompt("[SEARCH] > ", validator=number_validator(len(results))))
        anime_info = results[num].get_anime()
        get_video(session, anime_info)
    else:
        print("Not found")


@app.command("ongoing")
def ongoing():
    """Get new ongoings"""
    results = EXTRACTOR.ongoing()
    if len(results) > 0:
        print(*[f"{i} {r.name}" for i, r in enumerate(results)], sep="\n")
        print("choose title")
        session = app.new_prompt_session()
        num = int(session.prompt("[ONGOING] > ", validator=number_validator(len(results))))
        anime_info = results[num].get_anime()
        get_video(session, anime_info)
    else:
        print("Not found")
