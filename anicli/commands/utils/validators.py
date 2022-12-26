import re
from functools import partial
from typing import Callable, Union, Any, List, Optional

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator


RE_NUM_SLICE = re.compile(r"(\d+)-(\d+)")

__all__ = (
    "make_validator",
    "make_completer",
    "number_validator",
    "number_slice_validator",
)

def make_validator(function: Callable[..., bool], *args, **keywords) -> Validator:
    function = partial(function, *args, **keywords)
    return Validator.from_callable(function)


def make_completer(results: List[Any]) -> WordCompleter:
    words = [str(i) for i in range(len(results))] + ["..", "~"]
    meta_dict = {str(i): str(el) for i, el in enumerate(results)}
    meta_dict.update({"..": "back to prev state", "~": "return to root loop"})
    return WordCompleter(words=words,
                         meta_dict=meta_dict)


def _number_func(digit: str, max_len: int):
    return digit.isdigit() and 0 <= int(digit) < max_len or digit in {"..", "~"}


def number_validator(max_len: Union[int, list]) -> Validator:
    if isinstance(max_len, list):
        max_len = len(max_len)
    func = partial(_number_func, max_len=max_len)
    return Validator.from_callable(func, error_message=f"Should be integer and (0<=n<{max_len})")


def _number_slice_func(digit:str, max_len:int):
    return RE_NUM_SLICE.match(digit) or _number_func(digit, max_len)


def slice_digit(digit: str) -> Optional[slice]:
    if result := RE_NUM_SLICE.match(digit):
        return slice(*map(int, result.groups()))
    return None
    # raise TypeError(f"{digit} must me match `\d+-\d+` pattern")


def number_slice_validator(max_len: Union[int, list]) -> Validator:
    if isinstance(max_len, list):
        max_len = len(max_len)
    func = partial(_number_slice_func, max_len=max_len)
    return Validator.from_callable(func, error_message=f"Should be integer and (0<=n<={max_len}) or `\d+-\d+`")
