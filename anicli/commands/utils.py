from functools import partial
from typing import Callable, Union, Any, List

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator

from anicli.core import BaseState
from anicli.config import dp

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


CONCATENATE_ARGS = lambda *args: (" ".join(list(args)),)  # noqa


def on_exit_state(exc: BaseException):
    if isinstance(exc, (KeyboardInterrupt, EOFError)):
        print("KeyboardInterrupt, exit FROM State")
        dp.state_dispenser.finish()


def state_back(command: str, new_state: BaseState):
    if command == "..":
        dp.state_dispenser.set(new_state)
        return True
    return False


def state_main_loop(command: str):
    if command == "~":
        dp.state_dispenser.finish()
        return True
    return False

STATE_BACK = state_back
STATE_MAIN_LOOP = state_main_loop