"""Набор вспомогательных функций для рендера таблиц для всех команд поиска/проигрывания тайтлов"""

from typing import TYPE_CHECKING, Iterable, TypeVar

from rich import box, get_console
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from anicli.cli.ptk_lib.core.shortcuts import table_fill_limited_rows

if TYPE_CHECKING:
    from anicli_api.base import HttpMixin


console = get_console()
DIGITS_TUPLE = tuple(i for i in "0123456789")

T = TypeVar("T", bound="HttpMixin")


def render_table(title: str, results: Iterable[T]) -> None:
    table = Table(box=box.ROUNDED, title=title, title_justify="left", show_header=False)
    rows = [(str(i), str(result)) for i, result in enumerate(results, 1)]
    table_fill_limited_rows(table, *rows)

    console.print(table)


def render_update_notification(result: dict, console: Console) -> None:
    """
    Печатает уведомление об обновлениях в консоль (rich).
    result: {'anicli_ru': {...}, 'anicli_api': {...}}
    """
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
    table.add_column("Package", style="bold")
    table.add_column("Current")
    table.add_column("Latest")
    table.add_column("Status")

    for key in ("anicli_ru", "anicli_api"):
        info = result.get(key, {})
        cur = info.get("current_version") or "-"
        latest = info.get("latest_version") or "-"
        outdated = info.get("is_outdated", False)
        if outdated:
            status = Text("Available", style="bold yellow")
            status.append(" ⬆", style="yellow")
        else:
            status = Text("Up-to-date", style="green")
            status.append(" ✓", style="green")

        pkg_label = "anicli-ru" if key == "anicli_ru" else "anicli-api"
        table.add_row(pkg_label, str(cur), str(latest), status)

    header = Text("Update check", style="bold white on blue")
    panel = Panel(table, title=header, expand=False)
    console.print(panel)
    tip = Text("TIP: run `anicli-ru update` for upgrade all packages")
    console.print(tip)
