from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, get_type_hints, List, Union, Any
import logging
import inspect

from prompt_toolkit import PromptSession

from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.clipboard import Clipboard
from prompt_toolkit.completion import WordCompleter, Completer
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



def set_logger(level: int):
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=level)


@dataclass
class Command:
    keywords: list[str]
    meta: str
    func: Callable
    rule: Optional[Callable[..., bool]] = None
    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
    ctx: Optional[ABCDispatcher] = None

    def __contains__(self, item):
        return item in self.keywords

    @property
    def help(self):
        str_params = [str(param) for param in inspect.signature(self.func).parameters.values()
                      if not str(param).startswith("_") and ".base." not in str(param)]
        return ", ".join(str_params) + f" - {self.meta}"

    def __hash__(self):
        return hash(tuple(self.keywords))

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

        # check rule
        if self.rule and not self.rule(*args):
            return

        if self.ctx:
            self.func(self.ctx, *typed_args)
        else:
            self.func(*typed_args)


class ABCDispatcher(ABC):
    @abstractmethod
    def command(self,
                keywords: list[str],
                help_meta: Optional[str] = None,
                *,
                rule: Optional[Callable[..., bool]] = None,
                args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = None):
        ...

    @abstractmethod
    def add_command(self,
                    function: Callable,
                    keywords: list[str],
                    help_meta: Optional[str] = None,
                    *,
                    rule: Optional[Callable[..., bool]] = None,
                    args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = None):
        ...

    @abstractmethod
    def command_handler(self, command: str, *args):
        ...

    @abstractmethod
    def run(self):
        ...


class BaseDispatcher(ABCDispatcher):
    def __init__(self,
                 message: AnyFormattedText = "> ",
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
                 refresh_interval: float = 0,
                 ):
        self._commands: list[Command] = []

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

    def _update_word_completer(self) -> WordCompleter:
        words, meta_dict = [], {}
        for cls_command in self.list_commands:
            for word in cls_command.keywords:
                words.append(word)
                meta_dict[word] = cls_command.help
        logging.debug("Update word completer {} {}".format(words, meta_dict))
        return WordCompleter(words=words, meta_dict=meta_dict, sentence=True, ignore_case=True)

    def _has_keywords(self, keywords: list[str]) -> bool:
        words = []
        for c in self.list_commands:
            words.extend(c.keywords)
        return all(k in words for k in keywords)

    @staticmethod
    def _parse_prompt(text: str) -> tuple[str, list[str]]:
        command, args = text.split()[0], text.split()[1:]
        return command, args

    def _reset_prompt_session(self) -> None:
        self.session.completer = self._update_word_completer()
    def _loop(self) -> None:  # sourcery skip: use-fstring-for-formatting
        self._reset_prompt_session()
        while True:
            try:
                text = self.session.prompt()
                if not text:
                    continue
                command, args = self._parse_prompt(text)
                logging.debug("GET {} {}".format(command, args))
                if not self.command_handler(command, *args):
                    logging.debug("not found {} {}".format(command, args))
                    print("command", command, "not found")
            except (KeyboardInterrupt, EOFError) as e:
                logging.debug("KeyboardInterrupt | EOFError exit")
                exit(0)
            except Exception as e:
                logging.exception("{}\nInput `{}` get arguments `{} {}`".format(e, text, command, args))

    @property
    def list_commands(self) -> list[Command]:
        return self._commands

    def command(self,
                keywords: list[str],
                help_meta: Optional[str] = None,
                *,
                rule: Optional[Callable[..., bool]] = None,
                args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None) -> Callable:
        if self._has_keywords(keywords):
            logging.warning("commands {} has already added".format(keywords))
            return lambda *a: False

        if not help_meta:
            help_meta = ""

        def decorator(func):
            logging.debug("register command {} {}".format(keywords, help_meta))
            self._commands.append(Command(func=func, meta=help_meta, keywords=keywords,
                                          rule=rule, args_hook=args_hook))
            self._reset_prompt_session()
            return func
        return decorator

    @classmethod
    def new_prompt_session(cls,
               message: AnyFormattedText = "> ",
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
               refresh_interval: float = 0,
               ) -> PromptSession:
        return PromptSession(
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
            refresh_interval=refresh_interval)

    def remove_command(self, keyword: str) -> None:
        # sourcery skip: use-fstring-for-formatting
        for i, cls_command in enumerate(self._commands):
            if keyword in cls_command:
                logging.debug("Remove command {} {} {}".format(keyword, cls_command.keywords, cls_command.meta))
                self._commands.pop(i)
                return
        logging.debug("command {} has not included".format(keyword))

    def add_command(self,
                    function: Callable,
                    keywords: list[str],
                    help_meta: Optional[str] = None,
                    *,
                    rule: Optional[Callable[..., bool]] = None,
                    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
                    ) -> Callable[[Any], None] | None:
        # sourcery skip: use-fstring-for-formatting
        if self._has_keywords(keywords):
            logging.warning("commands {} has already added".format(keywords))
            return lambda *a: None

        if not help_meta:
            help_meta = ""
        logging.debug("Add command {} {}".format(keywords, help_meta))
        self._commands.append(Command(func=function, meta=help_meta, keywords=keywords,
                                      rule=rule, ctx=self, args_hook=args_hook))
        self._reset_prompt_session()
        return None

    def command_handler(self, command: str, *args) -> bool:
        # sourcery skip: use-fstring-for-formatting
        for cls_command in self._commands:
            if command.lower() in cls_command:
                logging.debug("Found {}".format(cls_command.keywords,))
                cls_command(*args)
                self._reset_prompt_session()
                return True
        return False

    def run(self, debug: bool = False) -> None:
        if debug:
            logging.basicConfig(format='%(asctime)s %(message)s',
                                level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(asctime)s %(message)s',
                                level=logging.WARNING)
        self._loop()

