"""Command management: registration and execution with sub_commands support"""

import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator
from rich import get_console

from .middleware import CommandMiddlewareManager
from .types import T_VALIDATOR, CommandContext, CommandRoute

if TYPE_CHECKING:
    from .application import Application

# magic variables if it not annotated
FALLBACK_CONTEXT_NAMES = ("ctx", "context", "_ctx", "_context")


class CommandManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.commands: Dict[str, CommandRoute] = {}
        self._command_aliases: Dict[str, str] = {}
        self.console = get_console()

    def register(self, route: CommandRoute) -> None:
        """Register a command and its aliases"""
        self.commands[route.key] = route
        for alias in route.aliases:
            if alias in self.commands or alias in self._command_aliases:
                msg = f"Alias '{alias}' already registered"
                raise ValueError(msg)
            self._command_aliases[alias] = route.key

    def get_command(self, key: str) -> Optional[CommandRoute]:
        """Get command by key or alias"""
        if key in self.commands:
            return self.commands[key]
        if key in self._command_aliases:
            return self.commands[self._command_aliases[key]]
        return None

    def _resolve_sub_command(self, route: CommandRoute, parts: List[str]) -> Tuple[CommandRoute, List[str]]:
        """
        Recursively resolve sub_command path.
        Returns (final_route, remaining_args)

        Example:
            parts = ["spam", "test", "arg"]
            If route has sub_command "spam", returns (spam_route, ["test", "arg"])
        """
        if not parts or not route.sub_commands:
            return route, parts

        # Check if first part matches a sub_command
        first_key = parts[0]
        for sub_cmd in route.sub_commands:
            if sub_cmd.key == first_key or first_key in sub_cmd.aliases:
                # Found sub_command, recurse
                return self._resolve_sub_command(sub_cmd, parts[1:])

        # No matching sub_command found - return current route with all parts
        return route, parts

    def _validate_input(self, validator: T_VALIDATOR, parsed_args: Any, ctx: CommandContext) -> bool:
        """
        Universal validator handler that supports:
        - Callable validators (sync)
        - prompt_toolkit Validator objects
        """
        if validator is None:
            return True

        # Handle prompt_toolkit Validator objects
        if isinstance(validator, Validator):
            try:
                # Create a Document object for validation
                document = Document(text=str(parsed_args))
                validator.validate(document)
                return True
            except ValidationError as e:
                self.console.print(f"[red]{e.message}[/red]")
                return False

        # Handle callable validators (original behavior)
        if callable(validator):
            return validator(parsed_args, ctx)

        # Unknown validator type
        self.console.print("[red]Invalid validator type[/red]")
        return False

    async def execute(self, cmd_key: str, raw_args: str) -> None:
        """Execute command with sub_command support"""
        route = self.get_command(cmd_key)
        if route is None:
            self.console.print(f"[red]Unknown command: {cmd_key}[/red]")
            return

        # Parse sub_commands from raw_args
        parts = raw_args.split() if raw_args.strip() else []
        final_route, remaining_parts = self._resolve_sub_command(route, parts)

        # Reconstruct args string from remaining parts
        final_args = " ".join(remaining_parts)

        ctx = CommandContext(
            app=self.app,
            command=final_route,
            args=final_args,
            _data=self.app.context._data,
        )

        async def _call_handler():
            parsed_args = final_route.parser(final_args) if final_route.parser else final_args

            # Validate using universal validator handler
            if final_route.validator:
                is_valid = self._validate_input(final_route.validator, parsed_args, ctx)
                if not is_valid:
                    # Validation failed - stop execution
                    return None

            sig = inspect.signature(final_route.handler)
            params = list(sig.parameters.values())

            expects_context = False
            if params:
                last_param = params[-1]
                ann = last_param.annotation

                # Check by type
                if ann is CommandContext:
                    expects_context = True
                elif hasattr(ann, "__origin__"):
                    # Handle Generic types like CommandContext[CtxT]
                    if (origin := getattr(ann, "__origin__", None)) and origin is CommandContext:
                        expects_context = True
                # Fallback: by parameter name
                elif last_param.name in FALLBACK_CONTEXT_NAMES:
                    expects_context = True

            args_to_pass = (parsed_args, ctx) if expects_context else (parsed_args,)
            return await final_route.handler(*args_to_pass)

        await CommandMiddlewareManager.run_middleware_stack(ctx, final_route.middleware, _call_handler)
