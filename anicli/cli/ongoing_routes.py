from typing import List, Tuple, Union, cast

from anicli_api.base import BaseEpisode
from anicli_api.player.base import Video
from anicli_api.tools.helpers import get_video_by_quality
from rich import get_console

from anicli.common.anicli_api_helpers import videos_iterator
from anicli.common.mpv import play_mpv_batched_videos, play_mpv_video
from anicli.common.utils import is_arabic_digit

from .contexts import AnicliContext, OngoingContext
from .helpers.completer import make_ongoing_or_search_completer
from .helpers.episode_picker import parse_selection_mask
from .helpers.render import (
    render_table_anime_and_episodes_results,
    render_table_ongoings_results,
    render_table_sources_results,
)
from .helpers.validator import validate_prompt_episode, validate_prompt_index
from .ptk_lib import BaseFSM, CommandContext, command, fsm_route, fsm_state

CONSOLE = get_console()


@command("ongoing", help="get actual ongoings")
async def ongoing_command(_args: str, ctx: CommandContext[AnicliContext]):
    if not (extractor := ctx.data.get("extractor", None)):
        CONSOLE.print("[red]Extractor not initialized[/red]")
        return

    results = await extractor.a_ongoing()
    if not results:
        CONSOLE.print("No results found (maybe broken extractor or site?)")
        return
    render_table_ongoings_results(results)

    await ctx.app.start_fsm(
        "ongoing",
        "step_1",
        context={
            "results": results,
            "default_quality": ctx.data.get("quality", 2060),
            "mpv_opts": ctx.data.get("mpv_opts", ""),
            "m3u_size": ctx.data.get("m3u_size", 6),
        },
    )


@fsm_route("ongoing")
class OngoingFSM(BaseFSM[OngoingContext]):
    def _get_user_dynamic_validator(self, state_name: str, user_input: str) -> Union[bool, str]:
        """Validate user input based on the current FSM state."""
        if state_name == "step_1":
            # select ongoing result
            results = self.ctx.get("results", [])
            return validate_prompt_index(results, user_input)
        elif state_name == "step_2":
            # select episodes
            results = self.ctx.get("episodes", [])
            return validate_prompt_episode(results, user_input)
        elif state_name in ("step_3", "step_3_batched"):
            # select source (player, dubber)
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
            completions = [(str(i), result.title) for i, result in enumerate(episodes, 1)]
            return completions
        elif state_name in ("step_3", "step_3_batched"):
            sources = self.ctx.get("sources", [])
            # Add both index-based and title-based completions
            completions = [(str(i), result.title) for i, result in enumerate(sources, 1)]
            return completions
        return []

    @fsm_state("step_1", prompt_message="~/ongoing ")
    async def step_1(self, user_input: str):
        results = self.ctx.get("results", [])
        # Check if the input is an index (number)
        index = int(user_input)
        # transform human index to python
        result = results[index - 1]  # type: ignore (test in validators)

        anime = await result.a_get_anime()
        episodes = await anime.a_get_episodes()
        self.ctx["anime"] = anime
        self.ctx["episodes"] = episodes

        # insert template to step_2 state
        self.set_prompt_var("result", anime.title)

        render_table_anime_and_episodes_results(anime, episodes)

        await self.next_state("step_2")

    @fsm_state("step_2", prompt_message="~/ongoing/{result}/episode ")
    async def step_2(self, user_input: str):
        episodes = self.ctx.get("episodes", [])
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

            render_table_sources_results(episodes[value], sources)

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
            render_table_sources_results(first_episode, sources)
            await self.next_state("step_3_batched")

    # normal play (auto choice quality)
    @fsm_state("step_3", prompt_message="~/ongoing/{result}/episode/{episode} ")
    async def step_3(self, user_input: str):
        default_quality = self.ctx["default_quality"]  # type: ignore
        sources = self.ctx.get("sources", [])

        self.set_prompt_var("video", user_input)

        value = int(user_input) - 1
        source = sources[value]  # type: ignore

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
        await play_mpv_video(video_candidate, title, mpv_opts=opts)

        await self.go_back()

    # batch play (auto choice quality)
    @fsm_state("step_3_batched", prompt_message="~/ongoing/{result}/episode/{episode} ")
    async def step_3_batched(self, user_input: str):
        default_quality = self.ctx["default_quality"]  # type: ignore
        sources = self.ctx.get("sources", [])
        self.set_prompt_var("video", user_input)

        # transform human index to python
        value = int(user_input) - 1
        source = sources[value]  # type: ignore

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

        m3u_size = self.ctx["m3u_size"]  # type: ignore
        counter = 1
        playlist: List[Tuple[Video, str]] = []
        async for video, title in videos_iterator(
            selected,  # type: ignore
            initial_anime=self.ctx["anime"],  # type: ignore
            initial_video=video_candidate,
            initial_source=source,
        ):
            if counter % m3u_size == 0:
                await play_mpv_batched_videos(
                    [v[0] for v in playlist],  # videos
                    [v[1] for v in playlist],  # titles
                    mpv_opts=opts,
                )
                playlist.clear()
            playlist.append((video, title))
            counter += 1
        if playlist:
            await play_mpv_batched_videos(
                [v[0] for v in playlist],  # videos
                [v[1] for v in playlist],  # titles
                mpv_opts=opts,
            )
            playlist.clear()
        await self.go_back()
