from typing import Tuple


def parse_header_line(line: str) -> Tuple[str, str]:
    key, value = line.split('=', 1)
    return key, value
