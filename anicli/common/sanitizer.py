"""sanitizer core logic stolen from yt-dlp project and refactored

https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/utils/_utils.py#L613
"""

import re
import unicodedata


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
    s = re.sub(r"[0-9]+(?::[0-9]+)+", lambda m: m.group(0).replace(":", "_"), s)

    out = []
    for ch in s:
        o = ord(ch)
        # Remove control characters and DEL
        if o < 32 or o == 127:
            continue

        # Double quote: remove in restricted mode, otherwise replace with apostrophe
        if ch == '"':
            if restricted:
                continue
            out.append("'")
            continue

        # Remove question mark (as in original behavior)
        if ch == "?":
            continue
        # Replace some dangerous characters with underscore
        if ch in "/\\|*<>":
            out.append("_")
            continue
        # Replace colon with dash for readability (colons in timestamps already handled)
        if ch == ":":
            out.append("-")
            continue
        # In restricted mode, drop whitespace and non-ASCII characters
        if restricted:
            if ch.isspace():
                # drop whitespace in strict mode
                continue
            if o > 127:
                # drop non-ASCII (diacritics were removed earlier)
                continue
        # For is_id == True, keep most characters (we already removed controls above)
        out.append(ch)

    result = "".join(out)

    # If this is not an identifier, normalize spacing/underscores and trim edges
    if not is_id:
        # Collapse any whitespace into a single space
        # (in original yt-dlp sanitaizer replace to '_')
        result = re.sub(r"\s+", " ", result)
        # Collapse multiple underscores into one
        result = re.sub(r"_+", "_", result)
        # Strip leading/trailing dots, underscores and dashes
        result = result.strip("._- ")
        if not result:
            result = "_"

    return result
