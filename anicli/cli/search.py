from typing import TYPE_CHECKING, List
from urllib.parse import urlsplit

from eggella.fsm import IntStateGroup
from eggella.command import RawCommandHandler

from anicli import views
from anicli._validator import NumPromptValidator, AnimePromptValidator
from anicli._completion import word_completer, anime_word_completer
from anicli.cli.config import app, EXTRACTOR
from anicli.cli.player import MpvPlayer

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseSearch, BaseSource, BaseEpisode
    from anicli_api.player.base import Video


class SearchStates(IntStateGroup):
    EPISODE = 0
    SOURCE = 1
    VIDEO = 2
    SOURCE_SLICE = 3
    VIDEO_SLICE = 4


app.register_states(SearchStates)


@app.on_command("search", cmd_handler=RawCommandHandler())
def search(query: str):
    """find anime titles by query string"""
    results = EXTRACTOR.search(query)
    if not results:
        views.Message.not_found()
        return
    views.Message.show_results(results)
    choose = app.cmd.prompt("~/search ", completer=word_completer(results), validator=NumPromptValidator(results))
    if choose in ("..", "~"):
        return
    choose = int(choose)
    app.CTX["result"] = results[choose]
    app.fsm.run(SearchStates)


@app.on_state(SearchStates.EPISODE)
def choose_episode():
    result: "BaseSearch" = app.CTX["result"]
    anime: "BaseAnime" = result.get_anime()
    episodes: List["BaseEpisode"] = anime.get_episodes()
    if not episodes:
        views.Message.not_found_episodes()
        return app.fsm.finish()

    views.Message.show_results(episodes)
    choose = app.cmd.prompt("~/search/episode ",
                            completer=anime_word_completer(episodes),
                            validator=AnimePromptValidator(episodes))
    if choose in ("~", ".."):
        return app.fsm.finish()
    elif choose == "info":
        views.Message.show_anime_full_description(anime)
        return app.fsm.set(SearchStates.EPISODE)

    elif (parts := choose.split("-")) and len(parts) == 2 and all([p.isdigit() for p in parts]):
        span = slice(int(parts[0]), int(parts[1]))
        app.fsm["search"] = {"episode_slice": episodes[span]}
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    else:
        choose = int(choose)
        app.fsm["search"] = {"episode": episodes[choose]}
        app.fsm.set(SearchStates.SOURCE)


@app.on_state(SearchStates.SOURCE)
def choose_source():
    episode: "BaseEpisode" = app.fsm["search"]["episode"]
    sources: List["BaseSource"] = episode.get_sources()
    if not sources:
        views.Message.not_found()
        return app.fsm.prev()
    views.Message.show_results(sources)
    choose = app.cmd.prompt("~/search/episode/video ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()

    app.fsm["search"]["source"] = sources[int(choose)]
    app.fsm.set(SearchStates.VIDEO)


@app.on_state(SearchStates.VIDEO)
def choose_quality():
    source: "BaseSource" = app.fsm["search"]["source"]
    videos = source.get_videos()
    if not videos:
        views.Message.not_found()
        return app.fsm.prev()
    views.Message.show_results(videos)
    choose = app.cmd.prompt("~/search/episode/video/quality ",
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.prev()

    video = videos[int(choose)]
    app.fsm["search"]["video"] = video
    episode: "BaseEpisode" = app.fsm["search"]["episode"]
    MpvPlayer.play(video, title=episode.title)
    return app.fsm.set(SearchStates.EPISODE)


@app.on_state(SearchStates.SOURCE_SLICE)
def play_slice():
    # TODO refactoring
    episodes: List["BaseEpisode"] = app.fsm["search"]["episode_slice"]
    episode = episodes[0]
    sources: List["BaseSource"] = episode.get_sources()
    views.Message.show_results(sources)
    choose = app.cmd.prompt("~/search/episode/videoS ",
                            completer=word_completer(sources),
                            validator=NumPromptValidator(sources))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.EPISODE)
    else:
        app.fsm["search"]["source_slice"] = sources[int(choose)]
        return app.fsm.set(SearchStates.VIDEO_SLICE)



@app.on_state(SearchStates.VIDEO_SLICE)
def choose_quality_slice():
    first_source: "BaseSource" = app.fsm["search"]["source_slice"]
    episodes: List["BaseEpisode"] = app.fsm["search"]["episode_slice"]
    videos: List["Video"] = first_source.get_videos()

    views.Message.show_results(videos)
    choose = app.cmd.prompt("~/search/episode/videoS/quality ",
                            completer=word_completer(videos),
                            validator=NumPromptValidator(videos))
    if choose == "~":
        return app.fsm.finish()
    elif choose == "..":
        return app.fsm.set(SearchStates.SOURCE_SLICE)
    else:
        video = videos[int(choose)]
        visited = set()
        key = (urlsplit(video.url).netloc, video.type, video.quality, first_source.dub)  # TODO fix annotation

        for episode in episodes:
            if episode.num not in visited:
                for source in episode.get_sources():
                    for video in source.get_videos():
                        if key == (urlsplit(video.url).netloc, video.type, video.quality, source.dub):
                            visited.add(episode.num)
                            MpvPlayer.play(video, f"{episode.num} {episode.title} - {source.dub} "
                                                  f"[{urlsplit(video.url).netloc}]")
                            break
                    if episode.num in visited:
                        break
    app.fsm.set(SearchStates.EPISODE)


if __name__ == '__main__':
    app.loop()