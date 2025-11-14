from urllib.parse import urlsplit


def is_arabic_digit(s: str) -> bool:
    # str.isdigit() returns True for all number-like Unicode chars
    # >>> "١٢٣".isdigit()
    # True
    # >>> "¹".isdigit()
    # True
    return all("0" <= char <= "9" for char in s)


def is_arabic_slice(s: str, sep: str = "-") -> bool:
    parts = s.split(sep, 1)
    if len(parts) != 2:
        return False
    start, end = s.strip().split(sep, 1)
    if is_arabic_digit(start) and is_arabic_digit(end):
        return True
    return False


def str_to_slice(s: str, sep: str = "-") -> slice:
    if not is_arabic_slice(s, sep=sep):
        msg = "Not valid slice"
        raise TypeError(msg)
    start, end = s.strip().split(sep, 1)
    return slice(int(start), int(end))


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

    # 1. Must have scheme
    if not parts.scheme:
        msg = "Wrong proxy format: must include scheme (e.g., http, https, socks5)"
        raise ValueError(msg)

    # 2. Must have hostname
    if not parts.hostname:
        msg = "Wrong proxy format: must include hostname"
        raise ValueError(msg)

    # 3. Must have port
    if not parts.port:
        msg = "Wrong proxy format: must include port"
        raise ValueError(msg)

    # 4. Optional user/password
    userinfo = ""
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        userinfo += "@"

    # 5. Reconstruct normalized URL
    normalized = f"{parts.scheme}://{userinfo}{parts.hostname}:{parts.port}"
    return normalized
