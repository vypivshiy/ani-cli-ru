from rich import get_console

from .contexts import AnicliContext
from .helpers.render import render_table
from .ptk_lib import CommandContext, command

CONSOLE = get_console()


@command("ongoing", help="get actual ongoings")
async def ongoing_command(_args: str, ctx: CommandContext[AnicliContext]):
    if not (extractor := ctx.data.get("extractor", None)):
        CONSOLE.print("[red]Extractor not initialized[/red]")
        return

    results = await extractor.a_ongoing()
    if not results:
        CONSOLE.print("No results found (maybe broken extractor or site?)")
        return
    render_table("Ongoing results", results)

    await ctx.app.start_fsm(
        "ongoing",
        "step_1",
        context={
            "results": results,
            "default_quality": ctx.data.get("quality", 2060),
            "mpv_opts": ctx.data.get("mpv_opts", ""),
            "m3u_size": ctx.data.get("m3u_size", 6),
        },
    )
