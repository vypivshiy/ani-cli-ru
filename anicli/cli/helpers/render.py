"""Набор вспомогательных функций для рендера таблиц для всех команд поиска/проигрывания тайтлов"""

from typing import TYPE_CHECKING, Iterable

from rich import box, get_console
from rich.table import Table

from anicli.cli.ptk_lib.core.shortcuts import table_fill_limited_rows

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseOngoing, BaseSearch, BaseSource


console = get_console()
DIGITS_TUPLE = tuple(i for i in "0123456789")


def render_table_search_results(results: Iterable["BaseSearch"]) -> None:
    table = Table("no", "title", box=box.ROUNDED, title="Search results", title_justify="left")
    rows = [(f"[yellow]{i}[/yellow]", str(result)) for i, result in enumerate(results, 1)]
    table_fill_limited_rows(table, *rows)

    console.print(table)


def render_table_ongoings_results(results: Iterable["BaseOngoing"]) -> None:
    table = Table("no", "title", box=box.ROUNDED, title="Ongoing results", title_justify="left")
    rows = [(f"[yellow]{i}[/yellow]", str(result)) for i, result in enumerate(results, 1)]
    table_fill_limited_rows(table, *rows)

    console.print(table)


def render_table_anime_and_episodes_results(anime: "BaseAnime", episodes: Iterable["BaseEpisode"]) -> None:
    table = Table("no", "episode", box=box.ROUNDED, title=anime.title, title_justify="left")
    rows = [(f"[yellow]{i}[/yellow]", str(result)) for i, result in enumerate(episodes, 1)]
    table_fill_limited_rows(table, *rows)

    console.print(table)


def render_table_sources_results(episode: "BaseEpisode", sources: Iterable["BaseSource"]) -> None:
    if episode.title.strip().endswith(DIGITS_TUPLE):
        title = episode.title.strip()
    else:
        title = episode.title.strip()
    table = Table("no", "sources", box=box.ROUNDED, title=title, title_justify="left")
    rows = [(f"[yellow]{i}[/yellow]", str(result)) for i, result in enumerate(sources, 1)]
    table_fill_limited_rows(table, *rows)

    console.print(table)
