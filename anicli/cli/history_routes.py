from rich import get_console

from anicli.common import history

from .contexts import AnicliContext
from .helpers.render import render_table
from .ptk_lib import CommandContext, command

CONSOLE = get_console()


@command("history", help="show recently watched anime")
async def history_command(_args: str, ctx: CommandContext[AnicliContext]):
    if not (extractor := ctx.data.get("extractor", None)):
        CONSOLE.print("[red]Extractor not initialized[/red]")
        return
    results = history.load()
    if not results:
        CONSOLE.print("No results founded")
        return

    render_table("History results", results)

    await ctx.app.start_fsm(
        "history",
        "step_1",
        context={
            "extractor_name": ctx.data.get("extractor_name"),
            "results": results,
            "default_quality": ctx.data.get("quality", 2060),
            "mpv_opts": ctx.data.get("mpv_opts", ""),
            "m3u_size": ctx.data.get("m3u_size", 6),
        },
    )
