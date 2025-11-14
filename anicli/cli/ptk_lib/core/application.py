"""Main Application class"""

import inspect
from types import TracebackType
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Generic, List, Optional, Type, Union, cast

from prompt_toolkit.completion import Completer
from rich import box, get_console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.traceback import Traceback

from .command_manager import CommandManager
from .completer import ContextualCompleter, HybridFSMCompleter
from .event_manager import EventManager
from .fsm_manager import FSMManager
from .prompt_manager import PromptManager
from .shortcuts import async_yes_no_exit
from .types import T_VALIDATOR, AppContext, CommandContext, CommandRoute, CtxT, ErrorHandler, FSMRoute
from .validators import CallableWrapperValidator

if TYPE_CHECKING:
    from .fsm import BaseFSM

EVENT_CALLBACK = Callable[[AppContext[CtxT]], Awaitable[None]]


class Application(Generic[CtxT]):
    def __init__(
        self,
        routes: Optional[List[Union[Callable, Type["BaseFSM"]]]] = None,
        on_startup: Optional[List[EVENT_CALLBACK]] = None,
        on_close: Optional[List[EVENT_CALLBACK]] = None,
        initial_context: Optional[CtxT] = None,
        prompt_msg: str = "~ ",
        *,
        enable_default_commands: bool = True,
        debug: bool = False,
        rich_traceback: bool = True,
    ):
        self.console = get_console()

        # data is lazy initialized
        self.context: AppContext[CtxT] = AppContext(app=self, _data=initial_context or {})

        self.enable_default_commands = enable_default_commands
        self.debug = debug
        self.rich_traceback = rich_traceback
        self.max_frames_tb = 3

        self.command_manager = CommandManager(self)
        self.fsm_manager = FSMManager(self)
        self.prompt_manager = PromptManager(msg=prompt_msg)
        self.event_manager = EventManager(self)
        self.completer = ContextualCompleter(self)

        self._current_fsm: Optional["BaseFSM"] = None  # noqa: UP037 (circular imports)
        self._running = False

        # Exception handlers registry
        self._exception_handlers: List[ErrorHandler] = []
        self._register_default_exception_handler()

        if routes:
            for route in routes:
                self._register_route(route)

        # register events
        self.on_startup_events = on_startup or []
        self.on_close_events = on_close or []

        if self.enable_default_commands:
            self._register_default_commands()

    @property
    def current_fsm(self) -> Optional["BaseFSM"]:
        return self._current_fsm

    def _register_route(self, route_obj: Union[Callable, Type["BaseFSM"], "CommandRoute", "FSMRoute"]) -> None:
        """Register a route - can be decorated function, class, or route object directly"""
        # Handle CommandRoute objects directly
        if isinstance(route_obj, CommandRoute):
            route = route_obj
            self.command_manager.register(route)
            return

        # Handle FSMRoute objects directly
        if isinstance(route_obj, FSMRoute):
            self.fsm_manager.register(route_obj)
            return
        msg = f"Object {route_obj} is not a registered command or FSM"
        raise ValueError(msg)

    def _register_default_exception_handler(self) -> None:
        """Register default exception handler with rich traceback"""

        def default_handler(exc: Exception, context: str) -> Optional[str]:
            # Create rich traceback with maximum details
            rich_tb = Traceback.from_exception(
                type(exc), exc, exc.__traceback__, max_frames=self.max_frames_tb, suppress=[]
            )

            # Build detailed context information
            context_lines = []
            if context:
                context_lines.append(f"[bold cyan]Context:[/bold cyan] {context}")

            # Add information about current FSM state if applicable
            if self._current_fsm:
                fsm_info = [
                    f"[bold cyan]FSM Route:[/bold cyan] {self._current_fsm._route_key}",
                    f"[bold cyan]Current State:[/bold cyan] {self._current_fsm.context.current_state}",
                    f"[bold cyan]State History:[/bold cyan] {' → '.join(self._current_fsm.context.state_history)}",
                ]
                context_lines.extend(fsm_info)

            # Add FSM context data if available
            if self._current_fsm and self.current_fsm.app_ref.context:  # type: ignore
                context_lines.append("[bold cyan]FSM Data:[/bold cyan]")
                for key, value in list(self._current_fsm.context.data.items())[
                    : self.max_frames_tb
                ]:  # Limit to first 10 items
                    context_lines.append(f"  {key}: {value!r}")

            # Add application context data
            if self.context._data:
                context_lines.append("[bold cyan]App Data:[/bold cyan]")
                for key, value in list(self.context._data.items())[:5]:  # Limit to first 5 items
                    context_lines.append(f"  {key}: {value!r}")

            # Create context panel
            if context_lines:
                context_panel = Panel(
                    "\n".join(context_lines),
                    title="[bold yellow]Debug Context[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                )

            # Build the main error display
            error_title = f"[bold red]Exception: {type(exc).__name__}[/bold red]"
            if context:
                error_title += f" [dim]({context})[/dim]"

            main_panel = Panel(rich_tb, title=error_title, border_style="red", padding=(0, 1))

            # Display everything
            self.console.print(main_panel)
            if context_lines and locals().get("context_panel"):
                self.console.print(context_panel)  # type: ignore

            # Show additional debug information in debug mode
            if self.debug:
                # Show the actual line of code where exception occurred
                tb = exc.__traceback__
                tb = cast(TracebackType, tb)
                while tb.tb_next:
                    tb = tb.tb_next

                frame = tb.tb_frame
                if frame:
                    # Show source code around the error
                    try:
                        source_lines, line_no = inspect.getsourcelines(frame.f_code)
                        current_line = tb.tb_lineno
                        start = max(0, current_line - line_no - 3)
                        end = min(len(source_lines), current_line - line_no + 4)

                        if start < end:
                            source_snippet = "".join(source_lines[start:end])
                            syntax = Syntax(
                                source_snippet,
                                "python",
                                line_numbers=True,
                                start_line=line_no + start,
                                highlight_lines={current_line - line_no},
                                theme="monokai",
                            )
                            self.console.print(
                                Panel(
                                    syntax,
                                    title=f"[bold yellow]Source Code (around line {current_line})[/bold yellow]",
                                    border_style="yellow",
                                )
                            )
                    except (OSError, TypeError, IndexError):
                        pass  # Skip if we can't get source

            return None

        self.add_exception_handler(Exception, default_handler)

    def add_exception_handler(
        self, exception_type: Type[Exception], handler: Callable[[Exception, str], Optional[str]]
    ) -> None:
        """
        Register an exception handler for specific exception type.

        Args:
            exception_type: Type of exception to handle
            handler: Callable that receives (exception, context_str) and optionally returns a message

        Example:
            def handle_value_error(exc: ValueError, ctx: str):
                console.print(f"[yellow]Invalid value: {exc}[/yellow]")
                return None

            app.add_exception_handler(ValueError, handle_value_error)
        """
        self._exception_handlers.insert(0, ErrorHandler(exception_type=exception_type, handler=handler))

    def _handle_exception(self, exc: Exception, context: str = "") -> Optional[str]:
        """
        Handle exception using registered handlers.
        Returns optional message to display.
        """
        for error_handler in self._exception_handlers:
            if isinstance(exc, error_handler.exception_type):
                try:
                    return error_handler.handler(exc, context)
                except Exception as handler_exc:
                    # If handler fails, fall back to basic rich traceback
                    basic_tb = Traceback.from_exception(
                        type(handler_exc),
                        handler_exc,
                        handler_exc.__traceback__,
                    )
                    self.console.print(
                        Panel(basic_tb, title="[bold red]Exception Handler Failed[/bold red]", border_style="red")
                    )
                    return None
        return None

    def _register_default_commands(self) -> None:
        @self.command("help", help="Show help or help for a command")
        async def _help(args: str, _ctx: CommandContext):
            if args.strip():
                cmd = self.command_manager.get_command(args.strip())
                if cmd:
                    table = Table(show_header=False, title=f"{cmd.key} Commands", title_justify="left", box=box.ROUNDED)
                    table.add_row(f"[bold]{cmd.key}[/bold]", cmd.help)
                    self.console.print(table)
                    # depth=1
                    if cmd.sub_commands:
                        table = Table(show_header=False, title="Sub commands", title_justify="left", box=box.ROUNDED)
                        for sub_cmd in cmd.sub_commands:
                            table.add_row(f"[bold]{sub_cmd.key}[/bold]", sub_cmd.help)
                        self.console.print(table)
                    if cmd.usage:
                        self.console.print(f"Usage: {cmd.usage}")
                else:
                    self.console.print(f"[red]Unknown command: {args}[/red]")
            else:
                table = Table(show_header=False, title="Commands", title_justify="left", box=box.ROUNDED)
                for key, cmd in self.command_manager.commands.items():
                    table.add_row(f"[cyan]{key}[/cyan]", cmd.help)
                self.console.print(table)

        @self.command("exit", help="Exit the application")
        async def _exit(_: str, _ctx: CommandContext):
            if await async_yes_no_exit():
                self._running = False

        @self.command("clear", help="Clear the screen")
        async def _clear(_args: str, _ctx: CommandContext):
            self.console.clear()

    async def start_fsm(
        self,
        route_key: str,
        initial_state: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.current_fsm is not None:
            await self.current_fsm.on_fsm_exit()

        # AWAIT session creation (which enters initial state)
        fsm_session = await self.fsm_manager.create_fsm_session(
            route_key=route_key,
            initial_state=initial_state,
            context=context or {},
        )
        self._current_fsm = fsm_session

    def on_startup(self):
        """inline init startup event"""

        def wrapper(func):
            self.on_startup_events.append(func)

        return wrapper

    def on_close(self):
        """inline init startup event"""

        def wrapper(func):
            self.on_close_events.append(func)

        return wrapper

    def command(
        self,
        key: str,
        help: str = "",  # noqa: A002
        *,
        validator: Optional[T_VALIDATOR] = None,
        middleware: Optional[List[Callable]] = None,
        aliases: Optional[List[str]] = None,
        parser: Optional[Callable[[str], Any]] = None,
        completer: Optional[Completer] = None,
        usage: Optional[str] = None,
        examples: Optional[List[str]] = None,
        arguments: Optional[Dict[str, str]] = None,
    ):
        """inline init commands"""
        from .decorators import command as cmd_decorator  # noqa: PLC0415

        def wrapper(func):
            decorated = cmd_decorator(
                key=key,
                help=help,
                validator=validator,
                middleware=middleware,
                aliases=aliases,
                parser=parser,
                completer=completer,
                arguments=arguments,
                usage=usage,
                examples=examples,
            )(func)
            self._register_route(decorated)
            return func

        return wrapper

    async def run(self, cmd_key: Optional[str] = None, raw_args: Optional[str] = None) -> None:
        self._running = True
        activated_exec_cmd = True if cmd_key else False
        # start events
        async with self.event_manager.invoke_events():
            # main loop
            while self._running:
                try:
                    if activated_exec_cmd:
                        raw_args = raw_args or ""
                        cmd_key = cast(str, cmd_key)
                        await self.command_manager.execute(cmd_key, raw_args)
                        activated_exec_cmd = False
                    if self._current_fsm is not None:
                        await self._handle_fsm_input()
                    else:
                        await self._handle_global_input()
                except KeyboardInterrupt:
                    self.console.print("\n[red]Interrupted. Type 'exit' or press CTRL+D to quit.[/red]")
                except EOFError:
                    if await async_yes_no_exit():
                        self._running = False
                except Exception as e:
                    # Try custom handlers first
                    try:
                        self._handle_exception(e, context="Main loop")
                    except Exception:
                        # If handler re-raised, let it propagate
                        raise

            if self._current_fsm is not None:
                await self._current_fsm.on_fsm_exit()

    async def _handle_global_input(self) -> None:
        session = self.prompt_manager.configure_session(completer=self.completer)
        user_input = await session.prompt_async()

        if not user_input.strip():
            return

        parts = user_input.split(maxsplit=1)
        cmd_key = parts[0]
        raw_args = parts[1] if len(parts) > 1 else ""

        try:
            await self.command_manager.execute(cmd_key, raw_args)
        except Exception as e:
            try:
                self._handle_exception(e, context=f"Command: {cmd_key}")
            except Exception:
                # Exception re-raised by handler
                raise

    async def _handle_fsm_input(self) -> None:
        current_fsm = self.current_fsm
        if current_fsm is None:
            return

        route = self.fsm_manager.fsm_routes[current_fsm.route_key]
        state = current_fsm.context.current_state
        if not state or state.name not in route.states:
            return

        hybrid_completer = HybridFSMCompleter(self, state.completer)

        validator = None
        if state.validator or (current_fsm and hasattr(current_fsm, "get_dynamic_validator")):
            # dynamic validator inner BaseFSM.get_dynamic_validator()
            validator = CallableWrapperValidator(
                state.validator,  # static validator (absolute priority)
                current_fsm.context,
                current_fsm,
                state.name,
            )

        session = self.prompt_manager.configure_session(completer=hybrid_completer, validator=validator)
        user_input = await session.prompt_async()
        # navigation commands first
        if current_fsm.is_navigation_command(user_input):
            await current_fsm.handle_navigation_command(user_input)
            return

        # other input handle
        try:
            await self.fsm_manager.execute_state(current_fsm, state, user_input)
        except Exception as e:
            try:
                state_name = state.name
                self._handle_exception(e, context=f"FSM: {current_fsm.route_key}, State: {state_name}")
            except Exception:
                raise
