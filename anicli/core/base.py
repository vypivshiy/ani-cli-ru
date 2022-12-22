from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Callable, List, Union, Any, Iterable, Dict, Type
import logging

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as print

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

from anicli.core.command import Command


class ABCDispatcher(ABC):
    @abstractmethod
    def command(self,
                keywords: Union[list[str], str],
                help_meta: Optional[str] = None,
                *,
                rule: Optional[Callable[..., bool]] = None,
                args_hook: Optional[Callable[[tuple[str, ...]], tuple[str, ...]]] = None):
        ...

    @abstractmethod
    def add_command(self,
                    function: Callable,
                    keywords: Union[list[str], str],
                    help_meta: Optional[str] = None,
                    *,
                    completer: Optional[Completer] = None,
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
                 description: AnyFormattedText = "",
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

        self.description = description
        self._commands: list[Command] = []
        # {func_name: {error_name_1: func, error_name_2: func_2, ...}}

        self._loop_error_handler: Dict[str, Callable[[BaseException], None]] = {}

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

    def _update_word_completer(self) -> Completer:
        # sourcery skip: assign-if-exp, or-if-exp-identity
        words, meta_dict = [], {}
        for cls_command in self.commands:
            _, params = cls_command.help
            for word in cls_command.keywords:
                words.append(word)
                if params:
                    meta_dict[word] = f"{', '.join(params)} - {cls_command.meta}"
                else:
                    meta_dict[word] = cls_command.meta
        logging.debug("create word completer: {} {}".format(words, meta_dict))
        return WordCompleter(words=words, meta_dict=meta_dict, sentence=True, ignore_case=True)

    def _has_keywords(self, keywords: list[str]) -> bool:
        words = []
        for c in self.commands:
            words.extend(c.keywords)
        return all(k in words for k in keywords)

    @staticmethod
    def _parse_prompt(text: str) -> tuple[str, list[str]]:
        command, args = text.split()[0], text.split()[1:]
        logging.debug("command `{}` args: `{}`".format(command, args))
        return command, args

    def _reset_prompt_session(self) -> None:
        self.session.completer = self._update_word_completer()

    def _loop(self) -> None:  # sourcery skip: use-fstring-for-formatting
        print(self.description)
        self._reset_prompt_session()
        text, command, args = "", "", ()
        while True:
            try:
                text = self.session.prompt()
                if not text:
                    continue
                command, args = self._parse_prompt(text)
                logging.debug("GET {} {}".format(command, args))
                if not self.command_handler(command, *args):
                    logging.debug("not found {} {}".format(command, args))
                    print(f"command `{command}` not found")
            except BaseException as e:
                if error_handler_func := self._loop_error_handler.get(repr(e).split("(")[0]):
                    error_handler_func(e)
                else:
                    logging.exception("{}\nInput `{}` command `{} args {}`".format(e, text, command, args))
                    raise e

    def add_error_handler_loop(self, exception: Type[BaseException], function: Callable[[BaseException], None]):
        if not self._loop_error_handler.get(exception.__name__):
            self._loop_error_handler.update({exception.__name__: function})

    @property
    def commands(self) -> list[Command]:
        return self._commands

    def command(self,
                keywords: Union[list[str], str],
                help_meta: Optional[str] = None,
                *,
                rule: Optional[Callable[..., bool]] = None,
                args_hook:
                Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None) -> Callable[[Any], Command]:
        if isinstance(keywords, str):
            keywords = [keywords]

        if self._has_keywords(keywords):
            raise AttributeError(f"command `{keywords}` has already added")

        if not help_meta:
            help_meta = ""

        def decorator(func) -> Command:
            nonlocal help_meta
            logging.debug("register command {} {}".format(keywords, help_meta))

            if not help_meta:
                help_meta = func.__doc__ or ""

            command = Command(ctx=self,
                              func=func,
                              meta=help_meta,
                              keywords=keywords,  # type: ignore
                              rule=rule,
                              args_hook=args_hook)
            self._commands.append(command)
            self._reset_prompt_session()
            return command
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
        logging.debug("command {} not found".format(keyword))

    def add_command(self,
                    function: Callable,
                    keywords: Union[str, list[str]],
                    help_meta: Optional[str] = None,
                    *,
                    completer: Optional[Completer] = None,
                    rule: Optional[Callable[..., bool]] = None,
                    args_hook: Optional[Callable[[tuple[str, ...]], tuple[Any, ...]]] = None
                    ) -> Callable[[Any], None] | None:
        # sourcery skip: use-fstring-for-formatting
        if isinstance(keywords, str):
            keywords = [keywords]

        if self._has_keywords(keywords):
            logging.warning("command `{}` has already added".format(keywords))
            return lambda *a: None

        if not help_meta:
            help_meta = function.__doc__ or ""
        logging.debug("Add command {} {}".format(keywords, help_meta))
        self._commands.append(Command(ctx=self,
                                      func=function,
                                      meta=help_meta,
                                      keywords=keywords,
                                      rule=rule,
                                      args_hook=args_hook))
        self._reset_prompt_session()
        return None

    def command_handler(self, command: str, *args) -> bool:
        # sourcery skip: use-fstring-for-formatting
        for cls_command in self._commands:
            if command in cls_command:
                logging.debug("Found {}".format(cls_command.keywords, ))
                try:
                    if args:
                        cls_command(*args)
                    else:
                        cls_command()
                except BaseException as e:
                    cls_command.error_handler(e, *args)
                return True
        return False

    def run(self) -> None:
        self._loop()
