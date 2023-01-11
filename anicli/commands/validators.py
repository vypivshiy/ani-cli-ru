import re
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union, Iterable

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator

RE_NUM_SLICE = re.compile(r"(\d+)-(\d+)")

__all__ = (
    "make_validator",
    "enumerate_completer",
    "number_validator",
    "number_slice_validator",
    "slice_digit",
)


def make_validator(function: Callable[..., bool], *args, **keywords) -> Validator:
    function = partial(function, *args, **keywords)
    return Validator.from_callable(function)


def enumerate_completer(
        results: List[Any],
        *,
        whitelist_commands: Optional[Dict[str, str]] = None) -> WordCompleter:
    words = [str(i) for i in range(len(results))]
    meta_dict = {str(i): str(el) for i, el in enumerate(results)}
    if whitelist_commands:
        words.extend(list(whitelist_commands.keys()))
        meta_dict.update(whitelist_commands)
    return WordCompleter(words=words, meta_dict=meta_dict)


def _number_func(
    digit: str,
    max_len: int,
    whitelist_commands: Optional[Iterable[str]] = None):
    if not whitelist_commands:
        whitelist_commands = []
    return digit.isdigit() and 0 <= int(digit) < max_len or digit in whitelist_commands


def number_validator(
    max_len: Union[int, list],
    whitelist_commands: Optional[Iterable[str]] = None) -> Validator:
    if isinstance(max_len, list):
        max_len = len(max_len)
    if not whitelist_commands:
        whitelist_commands = []
    func = partial(_number_func, max_len=max_len, whitelist_commands=whitelist_commands)
    if whitelist_commands:
        err_msg = f"Should be integer (0<=n<{max_len}) or {whitelist_commands}"
    else:
        err_msg = f"Should be integer (0<=n<{max_len})"
    return Validator.from_callable(func, error_message=err_msg)


def _is_num_slice_or_int(digit: str, max_len: int, whitelist_commands: Iterable[str] = None):
    if not whitelist_commands:
        whitelist_commands = []
    return (
        RE_NUM_SLICE.match(digit)
        or _number_func(digit, max_len)
        or digit in whitelist_commands
    )


def slice_digit(digit: str) -> slice:
    if result := RE_NUM_SLICE.match(digit):
        start, end = result.groups()
        return slice(int(start)-1, int(end))
    raise TypeError(f"{digit} must me match (\d+-\d+) pattern")


def number_slice_validator(
    max_len: Union[int, list], whitelist_commands: Optional[Iterable[str]] = None) -> Validator:
    if isinstance(max_len, list):
        max_len = len(max_len)
    if not whitelist_commands:
        whitelist_commands = []

    func = partial(_is_num_slice_or_int, max_len=max_len, whitelist_commands=whitelist_commands)
    if whitelist_commands:
        err_msg = f"Should be integer (0<=n<{max_len}) or (\d+-\d+) match or {whitelist_commands}"
    else:
        err_msg = f"Should be integer (0<=n<{max_len}) or (\d+-\d+) match"
    return Validator.from_callable(func, error_message=err_msg)
