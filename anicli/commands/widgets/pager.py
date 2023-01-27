#!/usr/bin/env python
"""
A simple application that shows a Pager application.
"""
from typing import Any, Dict

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

__all__ = ("spawn_pager",)


def _dict_meta_to_text(meta_dict: Dict[str, Any]) -> str:
    text = ""
    for k, v in meta_dict.items():
        if isinstance(v, str) and len(v) < 48:
            text += f"{k} - {v}\n"
        elif isinstance(v, list):
            text += f"{k}:\n"
            for i, el in enumerate(v, 1):
                text += f"  * {i}] {el}\n"
        elif isinstance(v, dict):
            text+=_dict_meta_to_text(v)
        else:
            text += f"{k}\n    {v}\n"
    return text


def spawn_pager(metadata: Dict[str, Any]):
    """spawn pager with metadata"""
    bindings = KeyBindings()

    @bindings.add("c-c")
    @bindings.add("q")
    def _(event):
        """Quit."""
        event.app.exit()

    style = Style.from_dict(
        {
            "status": "reverse",
            "status.position": "#aaaa00",
            "status.key": "#ffaa00",
            "not-searching": "#888888",
        }
    )

    def get_statusbar_text():
        return [
            (
                "class:status.position",
                "{}:{}".format(
                    text_area.document.cursor_position_row + 1,
                    text_area.document.cursor_position_col + 1,
                ),
            ),
            ("class:status", " - Press "),
            ("class:status.key", "Ctrl-C"),
            ("class:status", " to exit, "),
            ("class:status.key", "/"),
            ("class:status", " for searching."),
        ]

    text = _dict_meta_to_text(metadata)
    search_field = SearchToolbar(
        text_if_not_searching=[("class:not-searching", "Press '/' to start searching.")]
    )

    text_area = TextArea(
        text=text,
        read_only=True,
        scrollbar=True,
        line_numbers=True,
        search_field=search_field,
    )

    root_container = HSplit(
        [
            # The top toolbar.
            Window(
                content=FormattedTextControl(get_statusbar_text),
                height=D.exact(1),
                style="class:status",
            ),
            # The main content.
            text_area,
            search_field,
        ]
    )
    Application(
        layout=Layout(root_container, focused_element=text_area),
        key_bindings=bindings,
        enable_page_navigation_bindings=True,
        mouse_support=True,
        style=style,
        full_screen=True,
    ).run()
