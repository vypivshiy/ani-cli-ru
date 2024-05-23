from contextlib import suppress
from typing import TYPE_CHECKING, List

from eggella.command import RawCommandHandler
from eggella.fsm import IntStateGroup

from anicli import views
from anicli._completion import anime_word_choice_completer, word_choice_completer
from anicli._validator import AnimePromptValidator, NumPromptValidator
from anicli.cli.config import AnicliApp
from anicli.cli.player import run_video
from anicli.cli.slice_play import play_slice_playlist, play_slice_urls
from anicli.cli.video_utils import (
    get_preferred_human_quality_index,
    is_video_url_valid,
    slice_play_hash,
)
from anicli.utils import choice_human_index, choice_human_slice, create_title

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseSearch, BaseSource
    from anicli_api.player.base import Video


class SearchStates(IntStateGroup):
    START = 0
    EPISODE = 1
    SOURCE = 2
    VIDEO = 3
    SOURCE_SLICE = 4
    VIDEO_SLICE = 5


app = AnicliApp("search")
app.register_states(SearchStates)


@app.on_command("search", cmd_handler=RawCommandHandler())
def search(query: str):
    """find anime titles by query string"""
    app.CTX["search_query"] = query
    app.fsm.run(SearchStates)


@app.on_state(SearchStates.START)
def start_search():
    query = app.CTX["search_query"]
    results = app.CFG.EXTRACTOR.search(query)
    if not results:
        views.Message.not_found()
        return app.fsm.finish()
    views.Message.print_bold("[*] Search:")
    views.Message.show_results(results)
    choose = app.cmd.prompt(
        "~/search ", completer=word_choice_completer(results), validator=NumPromptValidator(results)
    )
    if choose in ("..", "~"):
        return app.fsm.finish()
    app.CTX["result"] = choice_human_index(results, int(choose))
    app.fsm.next()


@app.on_state(SearchStates.EPISODE)
def choose_episode():
    result: BaseSearch = app.CTX["result"]
    anime: BaseAnime = result.get_anime()

    if not anime:
        return app.fsm.prev()
    app.fsm["anime"] = anime

    episodes: List[BaseEpisode] = anime.get_episodes()
    if not episodes:
        views.Message.not_found_episodes()
        return app.fsm.finish()
    views.Message.print_bold("[*] Episodes:")
    views.Message.show_results(episodes)
    choose = app.cmd.prompt(
        "~/search/episode ", completer=anime_word_choice_completer(episodes), validator=AnimePromptValidator(episodes)
    )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.START)
    elif choose == "info":
        views.Message.show_anime_full_description(anime)
        return app.fsm.set(SearchStates.EPISODE)

    # 2 - text -> start_, end_ slice
    elif (parts := choose.split("-")) and len(parts) == 2 and all([p.isdigit() for p in parts]):  # noqa
        start, end = (int(p) for p in parts)
        app.fsm["search"] = {"episode_slice": choice_human_slice(episodes, start, end)}
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    else:
        app.fsm["search"] = {"episode": choice_human_index(episodes, int(choose))}
        app.fsm.set(SearchStates.SOURCE)


@app.on_state(SearchStates.SOURCE)
def choose_source():
    episode: BaseEpisode = app.fsm["search"]["episode"]
    sources: List[BaseSource] = episode.get_sources()
    if not sources:
        views.Message.not_found()
        return app.fsm.prev()

    views.Message.print_bold("[*] Sources:")
    views.Message.show_results(sources)
    choose = app.cmd.prompt(
        "~/search/episode/video ", completer=word_choice_completer(sources), validator=NumPromptValidator(sources)
    )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()
    app.fsm["search"]["source"] = choice_human_index(sources, int(choose))
    app.fsm.set(SearchStates.VIDEO)


@app.on_state(SearchStates.VIDEO)
def choose_quality():
    source: BaseSource = app.fsm["search"]["source"]
    videos = source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_human_quality_index(videos, app.CFG.MIN_QUALITY)

    if not videos:
        views.Message.not_found()
        return app.fsm.prev()

    views.Message.print_bold("[*] Videos:")
    views.Message.show_results(videos)
    choose = app.cmd.prompt(
        "~/search/episode/video/quality ",
        default=str(preferred_quality),
        completer=word_choice_completer(videos),
        validator=NumPromptValidator(videos),
    )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()
    while 1:
        # if url not valid - decrease quality
        video = choice_human_index(videos, int(choose))
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(SearchStates.VIDEO)
        views.Message.video_not_found()
        choose = int(choose) - 1

    app.fsm["search"]["video"] = video
    episode: BaseEpisode = app.fsm["search"]["episode"]
    anime: BaseAnime = app.fsm["anime"]
    title = create_title(anime, episode, source)

    run_video(video, app.CFG, title)
    return app.fsm.set(SearchStates.EPISODE)


@app.on_state(SearchStates.SOURCE_SLICE)
def play_slice():
    episodes: List[BaseEpisode] = app.fsm["search"]["episode_slice"]
    episode = episodes[0]
    sources: List[BaseSource] = episode.get_sources()
    views.Message.print_bold("[*] Sources <u>slice mode</u>:")
    views.Message.show_results(sources)
    choose = app.cmd.prompt(
        "~/search/episode/videoS ", completer=word_choice_completer(sources), validator=NumPromptValidator(sources)
    )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.EPISODE)
    else:
        app.fsm["search"]["source_slice"] = choice_human_index(sources, int(choose))
        return app.fsm.set(SearchStates.VIDEO_SLICE)


@app.on_state(SearchStates.VIDEO_SLICE)
def choose_quality_slice():
    first_source: BaseSource = app.fsm["search"]["source_slice"]
    episodes: List[BaseEpisode] = app.fsm["search"]["episode_slice"]
    videos: List[Video] = first_source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_human_quality_index(videos, app.CFG.MIN_QUALITY)

    views.Message.print_bold("[*] Video <u>slice mode</u>:")
    views.Message.show_results(videos)
    choose = app.cmd.prompt(
        "~/search/episode/videoS/quality ",
        default=str(preferred_quality),
        completer=word_choice_completer(videos),
        validator=NumPromptValidator(videos),
    )

    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    while 1:
        # if url not valid - decrease quality
        video = choice_human_index(videos, int(choose))
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(SearchStates.SOURCE_SLICE)
        views.Message.video_not_found()
        choose = int(choose) - 1

    cmp_key_hash = slice_play_hash(video, first_source)
    anime: BaseAnime = app.fsm["anime"]

    with suppress(KeyboardInterrupt):
        app.cmd.print_ft("SLICE MODE: Press q + CTRL+C for exit")
        if app.CFG.M3U_MAKE:
            play_slice_playlist(anime=anime, episodes=episodes, cmp_key_hash=cmp_key_hash, app=app)
        else:
            play_slice_urls(anime=anime, episodes=episodes, cmp_key_hash=cmp_key_hash, app=app)

    return app.fsm.set(SearchStates.EPISODE)
