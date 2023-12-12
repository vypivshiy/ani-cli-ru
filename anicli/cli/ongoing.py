from contextlib import suppress
from typing import TYPE_CHECKING, List, Optional

from anicli.cli.config import AnicliApp
from eggella.fsm import IntStateGroup

from anicli import views
from anicli._validator import NumPromptValidator, AnimePromptValidator
from anicli._completion import word_completer, anime_word_completer
from anicli.cli.video_utils import slice_playlist_iter, slice_play_hash, sort_video_by_quality, is_video_url_valid, \
    get_preferred_quality_index
from anicli.cli.player import run_video

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseOngoing, BaseSource, BaseEpisode
    from anicli_api.player.base import Video


class OngoingStates(IntStateGroup):
    START = 0
    EPISODE = 1
    SOURCE = 2
    VIDEO = 3
    SOURCE_SLICE = 4
    VIDEO_SLICE = 5


app = AnicliApp("ongoing")
app.register_states(OngoingStates)


@app.on_command("ongoing")
def ongoing():
    """get all available ongoing titles"""
    app.fsm.run(OngoingStates)


@app.on_state(OngoingStates.START)
def start_ongoing():
    results = app.CFG.EXTRACTOR.ongoing()
    if not results:
        views.Message.not_found()
        return app.fsm.finish()

    views.Message.print_bold("[*] Ongoings:")
    views.Message.show_results(results)
    choose = app.cmd.prompt(
        "~/ongoing ",
        completer=word_completer(results),
        validator=NumPromptValidator(results)
    )
    if choose in ("..", "~"):
        return app.fsm.finish()
    choose = int(choose)
    app.CTX["result"] = results[choose]
    app.fsm.next()


@app.on_state(OngoingStates.EPISODE)
def choose_episode():
    result: "BaseOngoing" = app.CTX["result"]
    anime: Optional["BaseAnime"] = result.get_anime()
    if not anime:
        return app.fsm.prev()

    episodes: List["BaseEpisode"] = anime.get_episodes()

    if not episodes:
        views.Message.not_found_episodes()
        return app.fsm.finish()
    views.Message.print_bold("[*] Episodes:")
    views.Message.show_results(episodes)
    choose = app.cmd.prompt("~/ongoing/episode ",
                            completer=anime_word_completer(episodes),
                            validator=AnimePromptValidator(episodes)
                            )
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(OngoingStates.START)
    elif choose == "info":
        views.Message.show_anime_full_description(anime)
        return app.fsm.current()

    elif (parts := choose.split("-")) and len(parts) == 2 and all([p.isdigit() for p in parts]):
        span = slice(int(parts[0]), int(parts[1]))
        app.fsm["ongoing"] = {"episode_slice": episodes[span]}
        return app.fsm.set(OngoingStates.SOURCE_SLICE)
    else:
        choose = int(choose)
        app.fsm["ongoing"] = {"episode": episodes[choose]}
        app.fsm.set(OngoingStates.SOURCE)


@app.on_state(OngoingStates.SOURCE)
def choose_source():
    episode: "BaseEpisode" = app.fsm["ongoing"]["episode"]
    sources: List["BaseSource"] = episode.get_sources()
    if not sources:
        views.Message.not_found()
        return app.fsm.prev()
    views.Message.print_bold("[*] Sources:")
    views.Message.show_results(sources)
    choose = app.cmd.prompt("~/ongoing/episode/video ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()

    app.fsm["ongoing"]["source"] = sources[int(choose)]
    app.fsm.set(OngoingStates.VIDEO)


@app.on_state(OngoingStates.VIDEO)
def choose_quality():
    source: "BaseSource" = app.fsm["ongoing"]["source"]
    videos = source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_quality_index(videos, app.CFG.MIN_QUALITY)

    if not videos:
        views.Message.not_found()
        return app.fsm.prev()
    views.Message.print_bold("[*] Videos:")
    views.Message.show_results(videos)
    choose = app.cmd.prompt("~/ongoing/episode/video/quality ",
                            default=str(preferred_quality),
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()

    while 1:
        video = videos[int(choose)]
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(OngoingStates.VIDEO)
        views.Message.video_not_found()
        choose = int(choose) - 1

    app.fsm["ongoing"]["video"] = video
    episode: "BaseEpisode" = app.fsm["ongoing"]["episode"]
    run_video(video, str(episode), player=app.CFG.PLAYER, use_ffmpeg=app.CFG.USE_FFMPEG_ROUTE)
    return app.fsm.set(OngoingStates.EPISODE)


@app.on_state(OngoingStates.SOURCE_SLICE)
def play_slice():
    episodes: List["BaseEpisode"] = app.fsm["ongoing"]["episode_slice"]
    episode = episodes[0]
    sources: List["BaseSource"] = episode.get_sources()

    views.Message.print_bold("[*] Sources <u>slice mode</u>:")
    views.Message.show_results(sources)

    choose = app.cmd.prompt("ongoing/episode/videoS ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(OngoingStates.EPISODE)
    else:
        app.fsm["ongoing"]["source_slice"] = sources[int(choose)]
        return app.fsm.set(OngoingStates.VIDEO_SLICE)


@app.on_state(OngoingStates.VIDEO_SLICE)
def choose_quality_slice():
    first_source: "BaseSource" = app.fsm["ongoing"]["source_slice"]
    episodes: List["BaseEpisode"] = app.fsm["ongoing"]["episode_slice"]
    videos: List["Video"] = first_source.get_videos(**app.CFG.httpx_kwargs())
    preferred_quality = get_preferred_quality_index(videos, app.CFG.MIN_QUALITY)

    views.Message.print_bold("[*] Videos <u>slice mode</u>:")
    views.Message.show_results(videos)

    choose = app.cmd.prompt("~/ongoing/episode/videoS/quality ",
                            default=str(preferred_quality),
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(OngoingStates.SOURCE_SLICE)
    while 1:
        video = videos[int(choose)]
        if is_video_url_valid(video):
            break
        elif int(choose) == 0:
            views.Message.not_found()
            return app.fsm.set(OngoingStates.SOURCE_SLICE)
        views.Message.video_not_found()
        choose = int(choose) - 1

    cmp_key_hash = slice_play_hash(video, first_source)
    with suppress(KeyboardInterrupt):
        for video, episode in slice_playlist_iter(episodes, cmp_key_hash, app.CFG):
            views.Message.print_bold("SLICE MODE: Press q + CTRL+C for exit")
            run_video(video, str(episode), player=app.CFG.PLAYER, use_ffmpeg=app.CFG.USE_FFMPEG_ROUTE)
    app.fsm.set(OngoingStates.EPISODE)
