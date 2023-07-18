from typing import Any, List, TYPE_CHECKING

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime


class Message:
    @staticmethod
    def not_found():
        print_formatted_text(
            HTML("<ascired>not found :(</ascired>")
        )

    @staticmethod
    def show_results(items_list: List[Any]):
        print_formatted_text(*[
            HTML(f"[<ansiyellow>{i}</ansiyellow>] {item}")
            for i, item in enumerate(items_list)
        ], sep="\n")

    @staticmethod
    def not_found_episodes():
        print_formatted_text(
            HTML("<ascired>episodes not available</ascired>")
        )

    @staticmethod
    def show_anime_full_description(anime: "BaseAnime"):

        text = f"""{anime.title} [{anime.alt_titles}]
Genres: {anime.genres}
Release: {anime.aired}
Episodes: {anime.episodes_available}/{anime.episodes_total}
Description:
    {anime.description}
"""

        search_field = SearchToolbar(text_if_not_searching=[("class:not-searching", "Press '/' to start searching.")])

        text_area = TextArea(
            text=text,
            read_only=True,
            scrollbar=True,
            search_field=search_field,
        )
        status_bar_text = [
            ("class:status", anime.title),
            ("class:status", " - Press "),
            ("class:status.key", "Ctrl-C or Q"),
            ("class:status", " to exit, "),
            ("class:status.key", "/"),
            ("class:status", " for searching."),
        ]
        root_container = HSplit(
            [
                # The top toolbar.
                Window(
                    content=FormattedTextControl(status_bar_text),  # type: ignore
                    height=D.exact(1),
                    style="class:status",
                ),
                # The main content.
                text_area,
                search_field,
            ]
        )

        # Key bindings.
        bindings = KeyBindings()

        @bindings.add("c-c")
        @bindings.add("q")
        def _(event):
            "Quit."
            event.app.exit()

        style = Style.from_dict(
            {
                "status": "reverse",
                "status.position": "#aaaa00",
                "status.key": "#ffaa00",
                "not-searching": "#888888",
            }
        )

        # create application.
        application = Application(  # type: ignore
            layout=Layout(root_container, focused_element=text_area),
            key_bindings=bindings,
            enable_page_navigation_bindings=True,  # type: ignore
            mouse_support=True,
            style=style,
            full_screen=True,
        )
        application.run()
