from functools import partial
from typing import Callable, Union, Any, List

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator


def make_validator(function: Callable[..., bool], *args, **keywords) -> Validator:
    function = partial(function, *args, **keywords)
    return Validator.from_callable(function)


def make_completer(results: List[Any]) -> WordCompleter:
    return WordCompleter(words=[str(i) for i in range(len(results))],
                         meta_dict={str(i): str(el) for i, el in enumerate(results)})


def _number_func(digit: str, max_len: int):
    return digit.isdigit() and 0 <= int(digit) < max_len


def number_validator(max_len: Union[int, list]) -> Validator:
    if isinstance(max_len, list):
        max_len = len(max_len)
    func = partial(_number_func, max_len=max_len)
    return Validator.from_callable(func, error_message=f"Should be integer and (0<=n<{max_len})")


CONCATENATE_ARGS = lambda *args: (" ".join(list(args)),) # noqa