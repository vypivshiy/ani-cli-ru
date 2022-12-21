import subprocess

from prompt_toolkit import PromptSession

from anicli_api.base import MetaVideo
from anicli_api.extractors import animego
from anicli.config import app
from anicli.utils import number_validator, make_completer

EXTRACTOR = animego.Extractor()
PLAYER = "mpv"


def mpv_attrs(video: MetaVideo) -> list[str]:
    if video.extra_headers:
        # --http-header-fields='Field1: value1','Field2: value2'
        headers = [f"{k}: {v}" for k, v in video.extra_headers.items()]
        headers = ",".join(headers)
        param = f'-http-header-fields="{headers}"'
        return [PLAYER, video.url, param]
    return [PLAYER, video.url]


def get_video(session: PromptSession, anime_info: animego.AnimeInfo):
    episodes = anime_info.get_episodes()
    print(*[f"[{i}] {e}" for i, e in enumerate(episodes)], sep="\n")
    num = int(session.prompt("[EPISODE] > ",
                             validator=number_validator(episodes),
                             completer=make_completer(episodes)))

    videos = episodes[num].get_videos()
    print("choose video host:")
    print(*[f"{i} {v}" for i, v in enumerate(videos)], sep="\n")
    num = int(session.prompt("[VIDEO] > ",
                             validator=number_validator(videos),
                             completer=make_completer(videos)))

    sources = videos[num].get_source()
    print("Quality:")
    print(*[f"{i} {v.type} {v.quality}" for i, v in enumerate(sources)], sep="\n")
    num = int(session.prompt("[QUALITY] > ",
                             validator=number_validator(sources),
                             completer=make_completer(sources)))

    args = mpv_attrs(sources[num])
    subprocess.run(" ".join(args), shell=True)


@app.command(["search", "find"], "search anime titles by query",
             args_hook=lambda *args: (" ".join(list(args)),))
def search(query: str):
    results = EXTRACTOR.search(query)
    if len(results) > 0:
        print(*[f"{i} {r}" for i, r in enumerate(results)], sep="\n")
        print("choose title")
        session = app.new_prompt_session()
        num = int(session.prompt("[SEARCH] > ",
                                 validator=number_validator(results),
                                 completer=make_completer(results)
                                 ))
        anime_info = results[num].get_anime()
        print(anime_info)
        get_video(session, anime_info)
    else:
        print("Not found")


@app.command("ongoing")
def ongoing():
    """Get new ongoings"""
    results = EXTRACTOR.ongoing()
    if len(results) > 0:
        print(*[f"{i} {r}" for i, r in enumerate(results)], sep="\n")
        print("choose title")
        session = app.new_prompt_session()
        num = int(session.prompt("[ONGOING] > ",
                                 validator=number_validator(results),
                                 completer=make_completer(results)
                                 ))
        anime_info = results[num].get_anime()
        get_video(session, anime_info)
    else:
        print("Not found")


@app.on_command_error()
def ongoing(error: Exception):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print("KeyboardInterrupt, back to menu")
        return


@app.on_command_error()
def search(error: Exception, query: str):
    if isinstance(error, (KeyboardInterrupt, EOFError)):
        print(f"`{query}` KeyboardInterrupt, back to menu")
        return
