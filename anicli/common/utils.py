from urllib.parse import urlsplit, urlunsplit


def is_arabic_digit(s: str) -> bool:
    # str.isdigit() returns True for all number-like Unicode chars
    # >>> "١٢٣".isdigit()
    # True
    # >>> "¹".isdigit()
    # True
    return s.isascii() and s.isdigit()


def is_arabic_slice(s: str, sep: str = "-") -> bool:
    """Check if a string is a valid 'start-end' numeric range."""
    parts = [p.strip() for p in s.split(sep, 1)]
    if len(parts) != 2:
        return False
    return is_arabic_digit(parts[0]) and is_arabic_digit(parts[1])


def str_to_slice(s: str, sep: str = "-") -> slice:
    """Convert '1-10' string to a Python slice object."""
    parts = [p.strip() for p in s.split(sep, 1)]
    if len(parts) != 2 or not all(is_arabic_digit(p) for p in parts):
        raise TypeError(f"'{s}' is not a valid arabic slice (e.g. '1-10')")

    return slice(int(parts[0]), int(parts[1]))


def validate_proxy_url(value: str) -> str:
    """
    Validate proxy URL.

    Expected formats:
      - scheme://user:password@host:port
      - scheme://host:port

    Raises:
        ValueError: if the URL is invalid or missing required parts.
    Returns:
        str: normalized URL if valid.
    """
    parts = urlsplit(value)

    if not parts.scheme:
        raise ValueError("Missing proxy scheme (e.g., http, https, socks5)")
    if not parts.hostname:
        raise ValueError("Missing proxy hostname")
    if parts.port is None:
        raise ValueError("Missing proxy port")

    # urlunsplit requires a 5-tuple: (scheme, netloc, path, query, fragment)
    # Reconstructing netloc ensures user:pass@host:port format is correct
    netloc = f"{parts.hostname}:{parts.port}"
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        netloc = f"{userinfo}@{netloc}"

    return urlunsplit((parts.scheme, netloc, "", "", ""))
