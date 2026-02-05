from rich import get_console

from .contexts import AnicliContext
from .helpers.render import render_table
from .ptk_lib import CommandContext, command

CONSOLE = get_console()


@command("search", help="search anime title by query")
async def search_command(query: str, ctx: CommandContext[AnicliContext]):
    if not (extractor := ctx.data.get("extractor", None)):
        CONSOLE.print("[red]Extractor not initialized[/red]")
        return
    results = await extractor.a_search(query)
    if not results:
        CONSOLE.print("No results founded")
        return

    render_table("Search results", results)

    await ctx.app.start_fsm(
        "search",
        "step_1",
        context={
            "query": query,
            "results": results,
            "default_quality": ctx.data.get("quality", 2060),
            "mpv_opts": ctx.data.get("mpv_opts", ""),
            "m3u_size": ctx.data.get("m3u_size", 6),
        },
    )
