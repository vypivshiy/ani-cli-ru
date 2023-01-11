from typing import Any, List

from prompt_toolkit import print_formatted_text as print_f
from prompt_toolkit.formatted_text import FormattedText

CONCATENATE_ARGS = lambda *args: (" ".join(list(args)),)  # noqa


def print_enumerate(things: List[Any]) -> None:
    for i, thing in enumerate(things, 0):
        text = FormattedText(
            [("", "["), ("ansigreen", f"{i}"), ("", "] "), ("ansiyellow", str(thing))]
        )
        print_f(text)