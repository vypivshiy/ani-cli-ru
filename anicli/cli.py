"""Preconfigured Cli class with help and exit commands"""
from typing import Optional

from anicli.base import BaseDispatcher


def _exit(_, _2):
    exit(1)


def _help(ctx: BaseDispatcher, _, command: Optional[str] = None):
    if command:
        for cls_command in ctx.list_commands:
            if command in cls_command:
                print(f"{cls_command.keywords} - {cls_command.help}")
                return
        print("command", command, "not found.\n\tusage `help` for get list available commands")
    else:
        for cls_command in ctx.list_commands:
            print(f"{cls_command.keywords} {cls_command.help}")


class CliApp(BaseDispatcher):
    def __init__(self):
        super().__init__()
        self.add_command(_exit, keywords=["exit", "quit"], help_meta="exit this app")
        self.add_command(_help, keywords=["help"], help_meta="show help message")
