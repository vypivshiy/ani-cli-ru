"""sanitizer core logic stolen from yt-dlp project and refactored

https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/utils/_utils.py#L613
"""

import re
import unicodedata

# Table for translation: map dangerous characters to safer alternatives
_DANGEROUS_CHARS_TABLE = str.maketrans(
    {
        '"': "'",
        ":": "-",
        "/": "_",
        "\\": "_",
        "|": "_",
        "*": "_",
        "<": "_",
        ">": "_",
        "?": None,  # Remove question marks
    }
)


def _deaccent(s: str) -> str:
    """
    Decompose characters and keep only basic ASCII characters.
    For example, "á" -> "a", "Æ" -> "AE" (where possible).
    Non-ASCII parts are removed.
    """
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def sanitize_filename(s: str, restricted: bool = False, is_id: bool = False) -> str:
    """
    Simplified filename sanitizer suitable for shell usage.

    Args:
        s: str
            Input string to sanitize.
        restricted: bool, optional
            If True, use a stricter sanitization:
            - remove diacritics,
            - drop non-ASCII characters,
            - remove whitespace.
        is_id: bool, optional
            If True, treat the input as an identifier and perform minimal changes
            (avoid collapsing or stripping characters aggressively).

    Returns:
        str
            A sanitized filename string (non-empty, falls back to "_" if needed).


    - In restricted mode, diacritics are removed (NFKD -> ASCII).
    - Timestamps like "01:23:45" are converted to "01_23_45".
    - Control characters and DEL are removed.
    - Quotes and some punctuation are replaced or removed to avoid shell issues.
    - If is_id is False, whitespace is collapsed into single underscores and
      repeated underscores are reduced; leading/trailing dots/underscores/dashes are stripped.
    """
    if not s:
        return ""

    # In restricted mode, remove diacritics and non-ASCII remains will be dropped later.
    if restricted:
        s = _deaccent(s)

    # Replace colons inside timestamps (e.g., "01:23:45" -> "01_23_45")
    s = re.sub(r"([0-9]+):([0-9]+):([0-9]+)", r"\1_\2_\3", s)

    # Remove control characters (0-31 and 127)
    s = re.sub(r"[\x00-\x1f\x7f]", "", s)

    if restricted:
        # In strict mode, keep only alphanumeric and basic punctuation
        # Drop everything that is not ASCII or is a space
        s = "".join(ch for ch in s if ord(ch) <= 127 and not ch.isspace())

    # Use translation table for fast character replacement
    s = s.translate(_DANGEROUS_CHARS_TABLE)

    # If this is not an identifier, normalize spacing/underscores and trim edges
    if not is_id:
        s = re.sub(r"\s+", " ", s)  # Collapse spaces
        s = re.sub(r"_+", "_", s)  # Collapse underscores
        s = s.strip("._- ")  # Trim edges

        if not s:
            return "_"

    return s
