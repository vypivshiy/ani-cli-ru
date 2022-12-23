from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Callable, Optional, List, Union

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import print_formatted_text as print

from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.clipboard import Clipboard
from prompt_toolkit.completion import Completer
from prompt_toolkit.cursor_shapes import AnyCursorShapeConfig
from prompt_toolkit.filters import FilterOrBool
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.history import History
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.shortcuts.prompt import PromptContinuationText
from prompt_toolkit.styles import BaseStyle, StyleTransformation
from prompt_toolkit.validation import Validator

if TYPE_CHECKING:
    from anicli.core.states import BaseState
    from anicli.core.command import Command
    from anicli.core.dispatcher import Dispatcher


class ABCPromptLoop(ABC):
    @abstractmethod
    def loop(self):
        ...


class PromptLoop(ABCPromptLoop):
    def __init__(self,
                 message: AnyFormattedText = "> ",
                 description: AnyFormattedText = "Press <tab> or type help for get commands",
                 *,
                 is_password: FilterOrBool = False,
                 complete_while_typing: FilterOrBool = True,
                 validate_while_typing: FilterOrBool = True,
                 enable_history_search: FilterOrBool = False,
                 search_ignore_case: FilterOrBool = False,
                 lexer: Optional[Lexer] = None,
                 enable_system_prompt: FilterOrBool = False,
                 enable_suspend: FilterOrBool = False,
                 enable_open_in_editor: FilterOrBool = False,
                 validator: Optional[Validator] = None,
                 completer: Optional[Completer] = None,
                 complete_in_thread: bool = False,
                 reserve_space_for_menu: int = 8,
                 complete_style: CompleteStyle = CompleteStyle.COLUMN,
                 auto_suggest: Optional[AutoSuggest] = None,
                 style: Optional[BaseStyle] = None,
                 style_transformation: Optional[StyleTransformation] = None,
                 swap_light_and_dark_colors: FilterOrBool = False,
                 color_depth: Optional[ColorDepth] = None,
                 cursor: AnyCursorShapeConfig = None,
                 include_default_pygments_style: FilterOrBool = True,
                 history: Optional[History] = None,
                 clipboard: Optional[Clipboard] = None,
                 prompt_continuation: Optional[PromptContinuationText] = None,
                 rprompt: AnyFormattedText = None,
                 bottom_toolbar: AnyFormattedText = None,
                 mouse_support: FilterOrBool = False,
                 input_processors: Optional[List[Processor]] = None,
                 placeholder: Optional[AnyFormattedText] = None,
                 key_bindings: Optional[KeyBindingsBase] = None,
                 erase_when_done: bool = False,
                 tempfile_suffix: Optional[Union[str, Callable[[], str]]] = ".txt",
                 tempfile: Optional[Union[str, Callable[[], str]]] = None,
                 refresh_interval: float = 0,):

        self.session: PromptSession = PromptSession(
            message=message,
            is_password=is_password,
            complete_while_typing=complete_while_typing,
            validate_while_typing=validate_while_typing,
            enable_history_search=enable_history_search,
            search_ignore_case=search_ignore_case,
            lexer=lexer,
            enable_system_prompt=enable_system_prompt,
            enable_suspend=enable_suspend,
            enable_open_in_editor=enable_open_in_editor,
            validator=validator,
            completer=completer,
            complete_in_thread=complete_in_thread,
            reserve_space_for_menu=reserve_space_for_menu,
            complete_style=complete_style,
            auto_suggest=auto_suggest,
            style=style,
            style_transformation=style_transformation,
            swap_light_and_dark_colors=swap_light_and_dark_colors,
            color_depth=color_depth,
            cursor=cursor,
            include_default_pygments_style=include_default_pygments_style,
            history=history,
            clipboard=clipboard,
            prompt_continuation=prompt_continuation,
            rprompt=rprompt,
            bottom_toolbar=bottom_toolbar,
            mouse_support=mouse_support,
            input_processors=input_processors,
            placeholder=placeholder,
            key_bindings=key_bindings,
            erase_when_done=erase_when_done,
            tempfile_suffix=tempfile_suffix,
            tempfile=tempfile,
            refresh_interval=refresh_interval
        )
        self.description = description
        self._commands: list[Command] = []
        self._states: Dict[BaseState, Callable[[], None]] = {}
        self._dp: Optional[Dispatcher] = None

    @property
    def commands(self):
        return self._commands

    def set_dispatcher(self, dp: Dispatcher):
        self._dp = dp

    def command_handler(self, keyword: str, *args: str):
        for cls_command in self._commands:
            if keyword in cls_command:
                try:
                    cls_command(*args)
                except BaseException as e:
                    cls_command.error_handler(e)
                return
        print(f"command `{keyword}` not found")

    def state_handler(self):
        while self._dp.state_dispenser.state:
            if func := self._states.get(self._dp.state_dispenser.state):
                func()

    def load_commands(self, commands: list[Command]):
        for c in commands:
            if c not in self._commands:
                self._commands.append(c)
        self.update_word_completer()

    def load_states(self, states: Dict[BaseState, Callable]):
        self._states = states

    def update_word_completer(self):
        words, meta_dict = [], {}
        for cls_command in self._commands:
            if cls_command.add_completer:
                meta = cls_command.help
                for word in cls_command.keywords:
                    words.append(word)
                    meta_dict[word] = meta

        self.session.completer = WordCompleter(
            words=words, meta_dict=meta_dict, sentence=True, ignore_case=True)

    @staticmethod
    def _parse_commands(text: str) -> tuple[str, tuple[str, ...]]:
        command, *args = text.split()
        return command, tuple(args)

    def loop(self):
        print(self.description)
        while True:
            self.state_handler()
            text = self.session.prompt()
            if not text:
                continue
            comma, args = self._parse_commands(text)
            self.command_handler(comma, *args)
