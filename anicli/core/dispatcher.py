from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, Type, Union

from anicli.core.command import Command
from anicli.core.prompt_loop import PromptLoop
from anicli.core.states import BaseState, StateDispenser


class ABCDispatcher(ABC):
    @abstractmethod
    def on_command(
        self,
        keywords: Union[list[str], str],
        meta: str = ...,
        *,
        rule: Optional[Callable[..., bool]] = ...,
        state: Optional[BaseState] = ...,
        args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = ...,
    ):
        ...

    @abstractmethod
    def run(self):
        ...


class Dispatcher(ABCDispatcher):
    def __init__(
        self, loop: PromptLoop, on_close: Callable[[], None] = lambda: print("Goodbye!")
    ):
        self.commands: list[Command] = []
        self.loop = loop
        self.state_dispenser = StateDispenser()
        self.states: Dict[BaseState, Callable] = {}
        self.on_error_states: Dict[BaseState, Callable[[BaseException], None]] = {}
        self.states_binds: Dict[BaseState, BaseState] = {}
        self._on_close = on_close

    def _has_keywords(self, keywords: list[str]) -> bool:
        words = []
        for c in self.commands:
            words.extend(c.keywords)
        return all(k in words for k in keywords)

    def on_state_handler(self, state: BaseState, on_error: Optional[Callable] = None):
        def decorator(func):
            if not self.states.get(state):
                self.states[state] = func

            if on_error and not self.on_error_states.get(state):
                self.on_error_states[state] = on_error
            return func

        return decorator

    def remove_command(self, keyword: str):
        for i, cls_command in enumerate(self.commands):
            if keyword in cls_command:
                self.commands.pop(i)
                return

    def on_command(
        self,
        keywords: Union[list[str], str],
        meta: str = "",
        *,
        rule: Optional[Callable[..., bool]] = None,
        state: Optional[BaseState] = None,
        args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = None,
    ):
        keywords = [keywords] if isinstance(keywords, str) else keywords

        if self._has_keywords(keywords):
            raise AttributeError(f"command `{keywords}` has already registered")

        def decorator(func) -> Command:
            command = Command(
                loop=self.loop,
                func=func,
                meta=meta,
                state=state,
                keywords=keywords,  # type: ignore
                rule=rule,
                args_hook=args_hook,
            )
            if state:
                self.states[state] = command
            self.commands.append(command)
            return command

        return decorator

    def run(self):
        self.loop.load_dispatcher(self)
        try:
            self.loop.loop()
        except (KeyboardInterrupt, EOFError):
            self._on_close()
