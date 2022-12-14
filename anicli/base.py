from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, get_type_hints
import logging
import inspect

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter


def set_logger(level: int):
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=level)


@dataclass
class Command:
    keywords: list[str]
    meta: str
    func: Callable
    rule: Callable[..., bool]
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

    def __call__(self, command: str, *args):
        t_hints = list(get_type_hints(self.func).values())
        signature = [p for p in inspect.signature(self.func).parameters.keys() if not p.startswith("_")]

        if len(t_hints) == 1 and len(signature) == 1:
            typed_args = [t_hints[0](arg) for arg in args]
        else:
            typed_args = list(args)

        if self.ctx:
            self.func(self.ctx, command, *typed_args)
        else:
            self.func(command, *typed_args)


class ABCDispatcher(ABC):
    @abstractmethod
    def command(self,
                keywords: list[str],
                help_meta: Optional[str] = None,
                rule: Optional[Callable[..., bool]] = None):
        ...

    @abstractmethod
    def add_command(self,
                    function: Callable,
                    keywords: list[str],
                    help_meta: Optional[str] = None,
                    rule: Optional[Callable[..., bool]] = None):
        ...

    @abstractmethod
    def command_handler(self, command: str, *args):
        ...

    @abstractmethod
    def run(self):
        ...


class BaseDispatcher(ABCDispatcher):
    def __init__(self,
                 prompt_session: PromptSession = PromptSession("> "),
                 message: str = "> "):
        self._commands: list[Command] = []
        self.session = prompt_session
        self._message = message

    def _update_word_completer(self) -> WordCompleter:
        words = []
        meta_dict = {}
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

    @property
    def list_commands(self) -> list[Command]:
        return self._commands

    def command(self, keywords: list[str], help_meta: Optional[str] = None, rule: Optional[Callable[..., bool]] = None):
        if self._has_keywords(keywords):
            logging.warning("commands {} has already added".format(keywords))
            return lambda *a: False

        if not rule:
            rule = lambda: True

        if not help_meta:
            help_meta = ""

        def decorator(func):
            logging.debug("register command {} {}".format(keywords, help_meta))
            self._commands.append(Command(func=func, meta=help_meta, keywords=keywords,
                                          rule=rule))
            self._reset_prompt_session()
            return func

        return decorator

    @staticmethod
    def _parse_prompt(text: str):
        command, args = text.split()[0], text.split()[1:]
        return command, args

    def remove_command(self, keyword: str):
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
                    rule: Optional[Callable[..., bool]] = None,
                    ):
        # sourcery skip: use-fstring-for-formatting
        if self._has_keywords(keywords):
            logging.warning("commands {} has already added".format(keywords))
            return lambda *a: False

        if not rule:
            rule = lambda command, *args: True

        if not help_meta:
            help_meta = ""
        logging.debug("Add command {} {}".format(keywords, help_meta))
        self._commands.append(Command(func=function, meta=help_meta, keywords=keywords,
                                      rule=rule, ctx=self))
        self._reset_prompt_session()
        return

    def command_handler(self, command: str, *args):
        # sourcery skip: use-fstring-for-formatting
        for cls_command in self._commands:
            if command.lower() in cls_command:
                logging.debug("Found {}".format(cls_command.keywords,))
                cls_command(command, *args)
                return True
        return False

    def _reset_prompt_session(self):
        self.session.message = self._message
        self.session.completer = self._update_word_completer()

    def _loop(self):  # sourcery skip: use-fstring-for-formatting
        self._reset_prompt_session()
        while True:
            try:
                text = self.session.prompt("> ")
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
                logging.exception("{}\ntext {}\ncommand {} {}".format(e, text, command, args))

    def run(self, debug: bool = False):
        if debug:
            set_logger(logging.INFO)
        else:
            set_logger(logging.WARNING)
        self._loop()
