from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import Callable, Optional, Any, get_type_hints, List, TYPE_CHECKING
import re

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completer

from anicli.core.defaults import ERROR_FRAGMENT, ERROR_STYLE
if TYPE_CHECKING:
    from anicli.core.base import ABCDispatcher


@dataclass
class BaseCommand:
    keywords: list[str]
    meta: str
    func: Callable
    rule: Optional[Callable[..., bool]] = None
    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
    ctx: Optional[ABCDispatcher] = None

    def __contains__(self, item):
        return item in self.keywords

    def __hash__(self):
        return hash(tuple(self.keywords))

    def __eq__(self, other: BaseCommand):
        return hash(other) == hash(self)

    def __call__(self, *args):
        if self.args_hook:
            args = self.args_hook(*args)

        t_hints = list(get_type_hints(self.func).values())
        signature = [p for p in inspect.signature(self.func).parameters.keys() if not p.startswith("_")]

        # try typing objects
        if len(t_hints) == 1 and len(signature) == 1:
            typed_args = [t_hints[0](arg) for arg in args]
        else:
            typed_args = list(args)
        try:
            if self.rule and not self.rule(*args):
                return

            if self.ctx:
                self.func(self.ctx, *typed_args)
            else:
                self.func(*typed_args)
        except TypeError as e:
            if missed_args := [
                a.replace("'_", "'") for a in re.findall(r"'\w+'", e.args[0])
            ]:
                print(ERROR_FRAGMENT, f"Missing {len(missed_args)} arguments: {', '.join(missed_args)}",
                      style=ERROR_STYLE)
            else:
                print(ERROR_FRAGMENT, "Command does not take arguments",
                      style=ERROR_STYLE)
            return


class Command(BaseCommand):
    @staticmethod
    def _is_valid_help_argument(param: str) -> bool:
        return not param.startswith("_") and not param.endswith("_") and ".base." not in param

    def _get_params_from_function(self) -> List[str]:
        return [str(param).split("=")[0].strip()
                for param in inspect.signature(self.func).parameters.values()
                if self._is_valid_help_argument(str(param))]

    @property
    def help(self):
        str_params = self._get_params_from_function()
        return ", ".join(str_params) + " | " + self.meta
