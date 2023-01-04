from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Type,
    TypeVar,
    get_args,
    get_type_hints,
)

if TYPE_CHECKING:
    from anicli.core.prompt_loop import PromptLoop
    from anicli.core.states import BaseState

T = TypeVar("T")


@dataclass
class BaseCommand:
    keywords: list[str]
    func: Callable
    loop: PromptLoop
    meta: str = ""
    rule: Optional[Callable[..., bool]] = None
    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
    state: Optional[BaseState] = None
    add_completer: bool = True

    def __post_init__(self):
        if not self.meta:
            self.meta = self.func.__doc__ or ""
        self.error_handler: Callable[
            [BaseException], None
        ] = self._default_error_handler

    def _default_error_handler(self, ex: BaseException):
        raise ex

    @property
    def types(self) -> List[Type]:
        return list(get_type_hints(self.func).values())

    @property
    def signature(self) -> List[str]:
        return [
            p
            for p in inspect.signature(self.func).parameters.keys()
            if not p.startswith("_")
        ]

    def __contains__(self, item):
        return item in self.keywords

    def __hash__(self):
        return hash(tuple(self.keywords))

    def __eq__(self, other):
        if isinstance(other, BaseCommand):
            return hash(other) == hash(self)
        raise TypeError(f"{other.__name__} should be 'Command', not {type(other)}")

    def _typing_args(self, *args):
        t_hints, signature = self.types, self.signature

        if len(t_hints) == 1 and len(signature) == 1:
            typed_args = []
            for arg in args:
                if len(get_args(t_hints[0])) > 1:
                    t_hints[0] = get_args(t_hints[0])[0]
                arg = t_hints[0](arg)
                typed_args.append(arg)
            typed_args = [t_hints[0](arg) for arg in args]

        elif len(t_hints) == len(signature):
            typed_args = []
            for (
                arg,
                type_,
            ) in zip(args, t_hints):
                if len(get_args(type_)) > 1:
                    type_ = get_args(type_)[0]
                arg = type_(arg)
                typed_args.append(arg)
        else:
            typed_args = list(args)
        return typed_args

    def __call__(self, *args):
        if self.args_hook:
            args = self.args_hook(*args)

        typed_args = self._typing_args(*args)

        try:
            if self.rule and not self.rule(*args):
                return
            self.func(*typed_args)
        except TypeError as e:
            if missed_args := [
                a.replace("'_", "'") for a in re.findall(r"'\w+'", e.args[0])
            ]:
                print(f"Missing {len(missed_args)} arguments: {', '.join(missed_args)}")
            else:
                print("Command does not take arguments")
            return

    def on_error(self):
        def decorator(function: Callable):
            self.error_handler = function
            return function

        return decorator


class Command(BaseCommand):
    @staticmethod
    def _is_valid_help_argument(param: str) -> bool:
        return (
            not param.startswith("_")
            and not param.endswith("_")
            and ".base." not in param
        )

    def _get_params_from_function(self) -> list[str]:
        return [
            str(param).split("=")[0].strip()
            for param in inspect.signature(self.func).parameters.values()
            if self._is_valid_help_argument(str(param))
        ]

    @property
    def meta_completer(self):
        if str_params := self._get_params_from_function():
            return f"{', '.join(self.keywords)} - {self.meta}; Params: {', '.join(str_params)}"
        return f"{', '.join(self.keywords)} - {self.meta}"

    @property
    def help(self) -> str:
        msg = f"{', '.join(self.keywords)} - {self.meta}"
        if str_params := self._get_params_from_function():
            msg += "\nParams:\n\t"
            for name_a_param in str_params:
                if len((args := name_a_param.split(":"))) == 2:
                    msg += f"{args[0]}: [{args[1].strip()}]\n\t"
                else:
                    msg += f"[{args[0]}]\n\t"
            return msg
        msg += "\n"
        # return f'{", ".join(self.keywords)}; params: {", ".join([p.split(":") for p in str_params])} - {self.meta}'
        return msg
