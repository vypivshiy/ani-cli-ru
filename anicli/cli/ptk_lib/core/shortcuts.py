from typing import TYPE_CHECKING, Awaitable, Tuple, Union

from prompt_toolkit.formatted_text import merge_formatted_text
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts.prompt import PromptSession
from rich import box, get_console
from rich.console import RenderableType
from rich.table import Table

if TYPE_CHECKING:
    from anicli.cli.ptk_lib import CommandContext

E = KeyPressEvent
console = get_console()


def create_confirm_session(
    message: str,
    suffix: str = " ([y]/n) ",
    default_key: Union[str, Keys] = Keys.Enter,
    *,
    default_value: bool = True,
) -> PromptSession[bool]:
    """Create a confirmation prompt session with customizable key bindings.

    Args:
        message: The confirmation message to display
        suffix: Suffix to append to the message (default " ([y]/n) ")
        default_key: Key that triggers the default value (default Enter key)
        default_value: Default return value if default_key is pressed (default True)

    Returns:
        PromptSession[bool]: A configured prompt session that returns a boolean
    """
    bindings = KeyBindings()

    @bindings.add("y")
    @bindings.add("Y")
    def yes(event: E) -> None:
        session.default_buffer.text = "y"
        event.app.exit(result=True)

    @bindings.add("д")
    @bindings.add("Д")
    def yes_cyrillic(event: E) -> None:
        session.default_buffer.text = "д"
        event.app.exit(result=True)

    @bindings.add("n")
    @bindings.add("N")
    def no(event: E) -> None:
        session.default_buffer.text = "n"
        event.app.exit(result=False)

    @bindings.add("н")
    @bindings.add("Н")
    def no_cyrillic(event: E) -> None:
        session.default_buffer.text = "н"
        event.app.exit(result=False)

    @bindings.add(default_key)
    def _default(event: E) -> None:
        event.app.exit(result=default_value)

    @bindings.add(Keys.Any)
    def _(__: E) -> None:
        pass

    complete_message = merge_formatted_text([message, suffix])
    session: PromptSession[bool] = PromptSession(complete_message, key_bindings=bindings)
    return session


def async_yes_no_exit(message: str = "Do you really want to exit?") -> Awaitable[bool]:
    """Create and run an asynchronous yes/no confirmation prompt for exit.

    Args:
        message: The confirmation message to display (default "Do you really want to exit?")

    Returns:
        Awaitable[bool]: An awaitable that returns True if user confirms, False otherwise
    """
    return create_confirm_session(message).prompt_async()


def yes_no_exit(message: str = "Do you really want to exit?") -> bool:
    """Create and run a synchronous yes/no confirmation prompt for exit.

    Args:
        message: The confirmation message to display (default "Do you really want to exit?")

    Returns:
        bool: True if user confirms, False otherwise
    """
    return create_confirm_session(message).prompt()


def print_subcommand_help(ctx: "CommandContext"):
    """Print help information for subcommands of a given command context.

    Args:
        ctx: The command context containing the command with subcommands
    """
    cmd_route = ctx.command

    if cmd_route.sub_commands:
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description")

        for sub_cmd in cmd_route.sub_commands:
            table.add_row(sub_cmd.key, sub_cmd.help)

        console.print(table)
        console.print("\n[dim]Usage: config <subcommand> [args][/dim]")
    else:
        console.print("[yellow]No subcommands available[/yellow]")


def table_fill_limited_rows(
    table: Table, *rows: Tuple[RenderableType, ...], max_view_count: int = 25, end_view_count: int = 3
) -> None:
    """Fill a Rich table with rows, limiting the number displayed with a summary for large datasets.

    Args:
        table: The Rich Table to fill
        rows: Variable number of row tuples to add to the table
        max_view_count: Maximum number of rows to display (default 25)
        end_view_count: Number of rows to show at the end when truncating (default 3)
    """
    if len(rows) <= max_view_count:
        for row in rows:
            table.add_row(*row)
    else:
        start_count = max_view_count - end_view_count - 1  # -1 for the separator row
        start_count = max(start_count, 0)

        for i in range(start_count):
            table.add_row(*rows[i])

        hidden_count = len(rows) - start_count - end_view_count
        table.add_row(f"+{hidden_count} more", *["..."] * (len(rows[0]) - 1))

        for i in range(len(rows) - end_view_count, len(rows)):
            table.add_row(*rows[i])
