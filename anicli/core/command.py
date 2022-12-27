from __future__ import annotations
import re
from dataclasses import dataclass
import inspect
from typing import Callable, TYPE_CHECKING, Optional, Any, get_type_hints, List, Type, get_args, TypeVar

if TYPE_CHECKING:
    from anicli.core.states import BaseState
    from anicli.core.prompt_loop import PromptLoop

T = TypeVar("T")

@dataclass
class BaseCommand:
    keywords: list[str]
    meta: str
    func: Callable
    loop: PromptLoop
    rule: Optional[Callable[..., bool]] = None
    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
    state: Optional[BaseState] = None
    add_completer: bool = True

    def _default_error_handler(self, ex: BaseException):
        raise ex

    def __post_init__(self):
        self.error_handler: Callable[[BaseException], None] = self._default_error_handler

    @property
    def types(self) -> List[Type]:
        return list(get_type_hints(self.func).values())

    @property
    def signature(self) -> List[str]:
        return [p for p in inspect.signature(self.func).parameters.keys() if not p.startswith("_")]

    def __contains__(self, item):
        return item in self.keywords

    def __hash__(self):
        return hash(tuple(self.keywords))

    def __eq__(self, other):
        if isinstance(other, BaseCommand):
            return hash(other) == hash(self)
        raise TypeError(f"{repr(other)} is not Command")

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
            for arg, type_, in zip(args, t_hints):
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
            if missed_args := [a.replace("'_", "'") for a in re.findall(r"'\w+'", e.args[0])]:
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
        return not param.startswith("_") and not param.endswith("_") and ".base." not in param

    def _get_params_from_function(self) -> list[str]:
        return [str(param).split("=")[0].strip()
                for param in inspect.signature(self.func).parameters.values()
                if self._is_valid_help_argument(str(param))]

    @property
    def help(self) -> str:
        if str_params := self._get_params_from_function():
            return f'{", ".join(self.keywords)} params: {", ".join(str_params)} - {self.meta}'
        return f'{", ".join(self.keywords)} - {self.meta}'
