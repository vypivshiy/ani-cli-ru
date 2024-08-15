from typing import Iterable, TypeVar
from urllib.parse import urlsplit

import sys

T = TypeVar('T')


def float_to_hms(duration_float: float) -> str:
    """convert float or integet value to human-readable string (HH:MM:SS format)"""
    total_seconds = int(round(duration_float))

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def netloc(url: str) -> str:
    return urlsplit(url).netloc


def progress_bar(items: Iterable[T]) -> T:
    """
    Generator that yields each item with a rotating progress symbol.

    Args:
        items (list): List of items to process.

    Yields:
        item: Each item in the list.
    """
    symbols = ['|', '/', '-', '\\']
    num_symbols = len(symbols)

    for index, item in enumerate(items):
        symbol = symbols[index % num_symbols]
        sys.stdout.write(f"\r{symbol} {item}")
        sys.stdout.flush()
        yield item
