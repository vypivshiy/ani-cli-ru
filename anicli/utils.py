import itertools  # noqa
import re
import unicodedata
from typing import Sequence, TypeVar, TYPE_CHECKING

_T = TypeVar("_T")

if TYPE_CHECKING:
    from anicli_api.base import BaseAnime, BaseEpisode, BaseSource


def choice_human_index(collection: Sequence[_T], index: int) -> _T:
    return collection[index - 1]


def choice_human_slice(collection: Sequence[_T], start: int, end: int) -> Sequence[_T]:
    return collection[start - 1 : end]


def create_title(anime: "BaseAnime", episode: "BaseEpisode", source: "BaseSource") -> str:
    return f"{episode.num} {episode.title} {anime.title} ({source.title})"


class _NO_DEFAULT:  # noqa
    pass


# needed for sanitizing filenames in restricted mode
ACCENT_CHARS = dict(
    zip(
        "ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ",
        itertools.chain(
            "AAAAAA",
            ["AE"],
            "CEEEEIIIIDNOOOOOOO",
            ["OE"],
            "UUUUUY",
            ["TH", "ss"],
            "aaaaaa",
            ["ae"],
            "ceeeeiiiionooooooo",
            ["oe"],
            "uuuuuy",
            ["th"],
            "y",
        ),
    )
)


# TODO simplify, refactoring
# STOLEN from yt-dlp
# https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/utils/_utils.py#L613
def sanitize_filename(s, restricted=False, is_id=_NO_DEFAULT):  # noqa
    """Sanitizes a string so it could be used as part of a filename.
    @param restricted   Use a stricter subset of allowed characters
    @param is_id        Whether this is an ID that should be kept unchanged if possible.
                        If unset, yt-dlp's new sanitization rules are in effect
    """
    if s == "":
        return ""

    def replace_insane(char):
        if restricted and char in ACCENT_CHARS:
            return ACCENT_CHARS[char]
        elif not restricted and char == "\n":
            return "\0 "
        elif is_id is _NO_DEFAULT and not restricted and char in '"*:<>?|/\\':
            # Replace with their full-width unicode counterparts
            return {"/": "\u29F8", "\\": "\u29f9"}.get(char, chr(ord(char) + 0xFEE0))
        elif char == "?" or ord(char) < 32 or ord(char) == 127:  # noqa: PLR2004
            return ""
        elif char == '"':
            return "" if restricted else "'"
        elif char == ":":
            return "\0_\0-" if restricted else "\0 \0-"
        elif char in "\\/|*<>":
            return "\0_"
        if restricted and (char in "!&'()[]{}$;`^,#" or char.isspace() or ord(char) > 127):  # noqa: PLR2004
            return "" if unicodedata.category(char)[0] in "CM" else "\0_"
        return char

        # Replace look-alike Unicode glyphs

    if restricted and (is_id is _NO_DEFAULT or not is_id):
        s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[0-9]+(?::[0-9]+)+", lambda m: m.group(0).replace(":", "_"), s)  # Handle timestamps
    result = "".join(map(replace_insane, s))
    if is_id is _NO_DEFAULT:
        result = re.sub(r"(\0.)(?:(?=\1)..)+", r"\1", result)  # Remove repeated substitute chars
        strip_re = r"(?:\0.|[ _-])*"
        result = re.sub(f"^\0.{strip_re}|{strip_re}\0.$", "", result)  # Remove substitute chars from start/end
    result = result.replace("\0", "") or "_"

    if not is_id:
        while "__" in result:
            result = result.replace("__", "_")
        result = result.strip("_")
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith("-_"):
            result = result[2:]
        if result.startswith("-"):
            result = "_" + result[len("-") :]
        result = result.lstrip(".")
        if not result:
            result = "_"
    return result
