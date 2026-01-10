import asyncio
from pathlib import Path
from typing import List

from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator
from rich import box, get_console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from anicli.common.extractors import dynamic_load_extractor_module, get_extractor_modules
from anicli.common.utils import validate_proxy_url

from .contexts import AnicliContext
from .ptk_lib import CommandContext, command, print_subcommand_help

__all__ = [
    "command_ask_gpt",
    "config_group_command",  # other - subcommands and not need register in application
]
console = get_console()
EXTRACTORS: List[str] = get_extractor_modules()


@command("info", help="print current settings")
async def cfg_info(_args: str, ctx: CommandContext):
    table = Table("key", "value", title="Settings", box=box.ROUNDED)
    table.add_column("")
    for key, value in ctx._data.items():
        if isinstance(value, (int, str, float)):
            table.add_row(key, str(value))
        elif isinstance(value, bool):
            table.add_row(key, "true" if value else "false")
        elif isinstance(value, Path):
            table.add_row(key, str(value))
    console.print(table)


class CfgExtractorValidator(Validator):
    def validate(self, document: Document):
        text = document.text
        if text.startswith("current"):
            if text != "current":
                raise ValidationError(message="'current' key not allowed arguments")
            return
        elif text.startswith("set"):
            _, arg = text.split(maxsplit=1)
            if not arg:
                raise ValidationError(message="'set' required extractor argument")
            elif arg not in EXTRACTORS:
                raise ValidationError(message=f"'{arg}' does not exists in extractors implementation")
            return
        raise ValidationError(message=f"Unknown arguments '{text}'")


# subcommands
@command(
    "extractor",
    help="extractor groups",
    completer={
        "set": {"_meta": "set new extractor", "_completions": EXTRACTORS},
        "current": {"_meta": "print current extractor"},
    },
    validator=CfgExtractorValidator(),
)
async def cfg_extractor(option: str, ctx: CommandContext[AnicliContext]):
    if option == "current":
        curr_extractor = ctx._data.get("extractor_name", None)
        console.print(f"Current extractor: [bold]{curr_extractor}[/bold]")
    elif option.startswith("set"):
        extractor_name = option.split()[-1]
        if extractor_name in EXTRACTORS:
            ctx._data["extractor_name"] = extractor_name
            http_client = ctx.data["extractor"].http  # type: ignore
            http_async_client = ctx.data["extractor"].http_async  # type: ignore

            ctx._data["extractor_instance"] = dynamic_load_extractor_module(extractor_name).Extractor
            ctx._data["extractor"] = ctx._data["extractor_instance"](
                http_client=http_client, http_async_client=http_async_client
            )
            console.print(f"Set new extractor: [bold]{extractor_name}[/bold]")
    else:
        console.print("failed resolve options")


class CfgProxyValidator(Validator):
    def validate(self, document: Document):
        text = document.text
        if text.startswith("remove"):
            if text != "remove":
                raise ValidationError(message="'remove' key not allowed arguments")
            return
        elif text.startswith("set"):
            _, arg = text.split(maxsplit=1)
            if not arg:
                raise ValidationError(message="'set' required proxy url")
            try:
                validate_proxy_url(arg)
            except ValueError:
                msg = f"'{arg}' wrong proxy format (should be https://user:password@host:port or socks5://user:password@host:port)"
                raise ValidationError(message=msg)  # noqa: B904
            return
        raise ValidationError(message=f"Unknown arguments '{text}'")


@command(
    "proxy",
    help="manage proxy settings",
    completer={
        "set": {"_meta": "set new proxy (format scheme://usr:password@host:port)"},
        "remove": {"_meta": "remove proxy"},
    },
)
async def cfg_proxy(option: str, ctx: CommandContext[AnicliContext]):
    if option == "remove":
        console.print("remove proxy!")
    elif option.startswith("set"):
        proxy = option.split()[-1]
        console.print("set new proxy:", proxy)


@command("config", help="app configuration", sub_commands=[cfg_extractor, cfg_info, cfg_proxy])
async def config_group_command(_args: str, ctx: CommandContext):
    print_subcommand_help(ctx)


# easter egg handler
@command(
    "ask-llm",
    help="[DEBUG] get answer and explanations from llm",
    completer=[
        "chatgpt",
        "claude",
        "deepseek",
        "qwen",
        "grok",
    ],
)
async def command_ask_gpt(prompt: str) -> None:
    # easter egg command
    parts = prompt.split(maxsplit=1)

    if len(parts) <= 1:
        console.print("[red]ERROR! prompt is empty[/red]")
        return

    if parts[0] not in ["chatgpt", "claude", "deepseek", "qwen", "grok"]:
        console.print(
            f'[red]ERROR! LLM provider {parts[0]} not exists! Expected: "chatgpt", "claude", "deepseek", "qwen", "grok"[/red]'
        )
        return

    import getpass, subprocess  # noqa

    # в тестах эта строка была зашифрованна через BASE64+rot-13, чтобы она отдаленно напоминала токен
    # но из-за даньшейшего выполнения этой строки в shell и для снятия недопомиманий шифрование было удалено
    OPENROUTER_KEY = 'mpv --title="LINUS DROIDVALDS INFECTED BILLION COMPUTERS BY VIRUS GCC IN SYSTEMD" --loop "https://github.com/vypivshiy/linus-infected-billions-pc-by-gcc-virus-in-systemd/raw/refs/heads/main/linus-infected-billions-pc-by-gcc-virus-in-systemd.mp4"'  # noqa
    prompt = parts[1]
    usr_name = getpass.getuser()
    console.print(f"[{usr_name}] >>> {prompt}")

    displayed_text = Text()
    live = Live(displayed_text, console=console, transient=True, refresh_per_second=12)
    live.start()

    dots_cycle = [".", "..", "...", ""]
    for _ in range(12):
        for dots in dots_cycle:
            animated_text = Text.from_markup(f"[green][{parts[0].upper()} 🤖][/green] >>> {dots}")
            live.update(animated_text)
            await asyncio.sleep(0.06)  # 0.06 * 4 (dots) = 0.24 sec/every iterate
    live.stop()
    subprocess.run(OPENROUTER_KEY, check=False, shell=True)  # noqa: S602


@command("throw-error", help="[DEBUG] demo show stacktrace if handler throw exception")
async def command_throw_error(_: str):
    raise ZeroDivisionError("Example exception and render stacktrace.")
