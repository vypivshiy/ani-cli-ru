from functools import partial
from typing import Callable

from prompt_toolkit.validation import Validator


def make_validator(function: Callable[..., bool], *args, **keywords) -> Validator:
    function = partial(function, *args, **keywords)
    return Validator.from_callable(function)


def _number_func(digit: str, max_len: int):
    return digit.isdigit() and 0 <= int(digit) < max_len


def number_validator(max_len: int) -> Validator:
    func = partial(_number_func, max_len=max_len)
    return Validator.from_callable(func, error_message=f"Should be integer and (0<=n<{max_len})")
