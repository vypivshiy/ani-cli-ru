from typing import List, Tuple, TypeVar, Union, cast
from urllib.parse import urlsplit

import attr
from anicli_api.base import BaseEpisode
from anicli_api.player.base import Video
from anicli_api.tools.helpers import get_video_by_quality
from rich import get_console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

from anicli.common import history
from anicli.common.anicli_api_helpers import videos_iterator
from anicli.common.mpv import MPVController
from anicli.common.utils import is_arabic_digit

from .contexts import Context, HistoryContext, OngoingContext, SearchContext
from .helpers.completer import make_ongoing_or_search_completer
from .helpers.episode_picker import parse_selection_mask
from .helpers.render import render_table
from .helpers.validator import validate_prompt_episode, validate_prompt_index
from .ptk_lib import BaseFSM, fsm_route, fsm_state

CONSOLE = get_console()

T = TypeVar("T", bound=Context)


class BaseAnimeFSM(BaseFSM[T]):
    ROUTE_NAME = "base"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_prompt_var("ROUTE_NAME", f"{self.ROUTE_NAME}")

    def _get_user_dynamic_validator(
        self, state_name: str, user_input: str
    ) -> Union[bool, str]:
        """Validate user input based on the current FSM state."""
        if state_name == "step_1":
            # selecting an anime from results.
            results = self.ctx.get("results", [])
            return validate_prompt_index(results, user_input)
        elif state_name == "step_2":
            # selecting an episode or range of episodes
            results = self.ctx.get("episodes", [])
            return validate_prompt_episode(results, user_input)
        elif state_name in ("step_3", "step_3_batched"):
            # selecting a video source
            results = self.ctx.get("sources", [])
            return validate_prompt_index(results, user_input)
        return True

    def _get_user_dynamic_completions(
        self,
        state_name: str,
        current_text: str,
    ) -> Union[List[str], List[Tuple[str, str]]]:
        """Create completers"""
        if state_name == "step_1":
            results = self.ctx.get("results", [])
            completions = make_ongoing_or_search_completer(results, current_text)
            return completions
        elif state_name == "step_2":
            episodes = self.ctx.get("episodes", [])
            # Add both index-based and title-based completions
            completions = [
                (str(i), str(result)) for i, result in enumerate(episodes, 1)
            ]
            return completions
        elif state_name in ("step_3", "step_3_batched"):
            sources = self.ctx.get("sources", [])
            # Add both index-based and title-based completions
            completions = [
                (str(i), f"{result.title} ({urlsplit(result.url).netloc})")
                for i, result in enumerate(sources, 1)
            ]
            return completions
        return []

    @fsm_state("step_1", prompt_message="~/{ROUTE_NAME} ")
    async def step_1(self, user_input: str):
        index = int(user_input)
        # transform human index to python
        result = self.ctx["results"][index - 1]  # type: ignore
        self.ctx["result_num"] = index - 1

        anime = await result.a_get_anime()
        episodes = await anime.a_get_episodes()
        self.ctx["anime"] = anime
        self.ctx["episodes"] = episodes

        self.set_prompt_var("result", anime.title)
        render_table(anime.title, episodes)

        await self.next_state("step_2")

    @fsm_state("step_2", prompt_message="~/{ROUTE_NAME}/{result}/episode ")
    async def step_2(self, user_input: str):
        episodes = self.ctx.get("episodes", [])
        if not episodes:
            CONSOLE.print("not available episodes")
            return await self.go_back()

        self.set_prompt_var("episode", f"[{user_input}]")

        # single episode choice
        if is_arabic_digit(user_input):
            # transform human index to python
            value = int(user_input) - 1

            sources = await episodes[value].a_get_sources()
            if not sources:
                CONSOLE.print("not available sources")
                return await self.go_back()
            self.ctx["episodes_num"] = value
            self.ctx["sources"] = sources

            render_table(episodes[value].title.strip(), sources)

            await self.next_state("step_3")
        else:
            mask = parse_selection_mask(user_input, len(episodes))
            selected = [x for x, m in zip(episodes, mask) if m]
            # required get first episode for pick source in next step
            first_episode = selected[0]
            sources = await first_episode.a_get_sources()
            if not sources:
                CONSOLE.print("not available sources")
                return await self.go_back()
            self.ctx["episodes_mask"] = mask
            self.ctx["sources"] = sources
            render_table(first_episode.title.strip(), sources)
            await self.next_state("step_3_batched")

    # normal play (auto choice quality)
    @fsm_state("step_3", prompt_message="~/{ROUTE_NAME}/{result}/episode/{episode} ")
    async def step_3(self, user_input: str):
        default_quality = self.ctx["default_quality"]  # type: ignore
        sources = self.ctx.get("sources", [])
        if not sources:
            CONSOLE.print("not available sources")
            return await self.go_back()
        self.set_prompt_var("video", user_input)

        value = int(user_input) - 1
        source = sources[value]

        videos = await source.a_get_videos()
        if not videos:
            CONSOLE.print("[red]video not founded[/red]")
            await self.go_back()
            return
        videos = cast(List[Video], videos)
        video_candidate = get_video_by_quality(videos, default_quality)
        anime = self.ctx["anime"]  # type: ignore
        ep_num = self.ctx["episodes_num"]  # type: ignore
        episode = self.ctx["episodes"][ep_num]  # type: ignore
        episode = cast(BaseEpisode, episode)
        title = f"{anime.title} - {episode.ordinal} {episode.title}"
        opts = self.ctx["mpv_opts"]  # type: ignore

        result_num = self.ctx["result_num"]  # type: ignore
        result = self.ctx["results"][result_num]  # type: ignore
        extractor_name = self.ctx["extractor_name"]  # type: ignore
        history.save(
            result,
            extractor_name,
            {f"{episode.ordinal} {episode.title}": source},
            f"{episode.ordinal} {episode.title}",
        )

        await MPVController(
            [video_candidate],
            [title],
            mpv_opts=opts,
            save_time=True,
        ).play()

        await self.go_back()

    # batch play (auto choice quality)
    @fsm_state(
        "step_3_batched", prompt_message="~/{ROUTE_NAME}/{result}/episode/{episode} "
    )
    async def step_3_batched(self, user_input: str):
        default_quality = self.ctx["default_quality"]  # type: ignore
        sources = self.ctx.get("sources", [])
        self.set_prompt_var("video", user_input)

        # transform human index to python
        value = int(user_input) - 1
        source = sources[value]

        videos = await source.a_get_videos()
        videos = cast(List[Video], videos)
        if not videos:
            CONSOLE.print("[red]video not founded[/red]")
            await self.go_back()
            return

        video_candidate = get_video_by_quality(videos, default_quality)

        mask = self.ctx["episodes_mask"]  # type: ignore
        selected = [x for x, m in zip(self.ctx["episodes"], mask) if m]  # type: ignore
        opts = self.ctx["mpv_opts"]  # type: ignore

        result_num = self.ctx["result_num"]  # type: ignore
        result = self.ctx["results"][result_num]  # type: ignore
        extractor_name = self.ctx["extractor_name"]  # type: ignore
        history.save(result, extractor_name)

        m3u_size = self.ctx["m3u_size"]  # type: ignore
        counter = 1
        playlist: List[Tuple[Video, str]] = []
        with Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=20),
            MofNCompleteColumn(),
            console=CONSOLE,
            transient=True,
        ) as progress:
            task_id = progress.add_task("Processing...", total=None)
            async for video, title, match_source in videos_iterator(
                selected,
                initial_anime=self.ctx["anime"],  # type: ignore
                initial_video=video_candidate,
                initial_source=source,
            ):
                progress.update(task_id, description=f"Fetch: {title[:20]}")
                progress.advance(task_id)

                source_data = attr.asdict(match_source)
                clean_source_data = {
                    k: v for k, v in source_data.items() if not k.startswith("_")
                }
                history_data = history.read()
                history_source: List[dict] = history_data[0]["source"]
                history_source.append(
                    {
                        "episode_title": title,
                        "title": clean_source_data.pop("title", "Unknown"),
                        "url": clean_source_data.pop("url", ""),
                        "data": clean_source_data,
                    }
                )
                history.update_last({"source": history_source})

                if counter % m3u_size == 0:
                    progress.stop()
                    CONSOLE.print(f"Running playlist batch {counter // m3u_size}")
                    await MPVController(
                        [v[0] for v in playlist],  # video
                        [v[1] for v in playlist],  # str title
                        mpv_opts=opts,
                        save_time=True,
                    ).play()

                    playlist.clear()
                    progress.start()
                playlist.append((video, title))
                counter += 1
            # Финальный запуск
            if playlist:
                progress.stop()
                CONSOLE.print("Running final playlist batch")
                await MPVController(
                    [v[0] for v in playlist],  # video
                    [v[1] for v in playlist],  # str title
                    mpv_opts=opts,
                    save_time=True,
                ).play()

                playlist.clear()
        await self.go_back()


@fsm_route("search")
class SearchFSM(BaseAnimeFSM[SearchContext]):
    ROUTE_NAME = "search"


@fsm_route("ongoing")
class OngoingFSM(BaseAnimeFSM[OngoingContext]):
    ROUTE_NAME = "ongoing"


@fsm_route("history")
class HistoryFSM(BaseAnimeFSM[HistoryContext]):
    ROUTE_NAME = "history"

    @fsm_state("step_1", prompt_message="~/{ROUTE_NAME} ")
    async def step_1(self, user_input: str):
        index = int(user_input)

        history_data = history.read()[index - 1]
        time = history_data["time"]
        if time is not None:
            minutes, seconds = divmod(time, 60)
            continue_ep = input(
                f"Do you want to continue ep {history_data['episode']} at {minutes:02d}:{seconds:02d}\n(y/n): "
            )
            if continue_ep == "y":
                source = history.load_source(history_data, history_data["episode"])
                default_quality = self.ctx["default_quality"]  # type: ignore
                videos = await source.a_get_videos()
                if not videos:
                    CONSOLE.print("[red]video not founded[/red]")
                    await self.go_back()
                    return
                videos = cast(List[Video], videos)
                video_candidate = get_video_by_quality(videos, default_quality)
                opts = self.ctx["mpv_opts"] + f"--start={time}"  # type: ignore
                await MPVController(
                    [video_candidate],
                    [history_data["episode"]],
                    mpv_opts=opts,
                    save_time=True,
                ).play()

        # transform human index to python
        result = self.ctx["results"][index - 1]  # type: ignore
        self.ctx["result_num"] = index - 1

        anime = await result.a_get_anime()
        episodes = await anime.a_get_episodes()
        self.ctx["anime"] = anime
        self.ctx["episodes"] = episodes

        self.set_prompt_var("result", anime.title)
        render_table(anime.title, episodes)

        await self.next_state("step_2")
