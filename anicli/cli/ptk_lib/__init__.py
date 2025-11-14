"""High-level API for ptk_lib — prompt toolkit framework with FSM"""

# Core application
from .core.application import Application

# Decorators (main API)
from .core.decorators import command, fsm_route, fsm_state
from .core.shortcuts import print_subcommand_help

# Types for typing support
from .core.types import (
    AppContext,
    CommandContext,
    FSMContext,
    CommandRoute,
    FSMRoute,
    FSMState,
)

# Optional: expose BaseFSM for inheritance
from .core.fsm import BaseFSM

# Optional: expose Completer helpers
from .core.completer import NestedCompleterWithMeta

# Optional: expose validators (user implements them, but we provide base idea)
# (Validators are typically user-defined callables)

__all__ = [
    # Main classes
    "Application",
    "BaseFSM",
    # Decorators
    "command",
    "fsm_route",
    "fsm_state",
    # Types (for annotations)
    "AppContext",
    "CommandContext",
    "FSMContext",
    "CommandRoute",
    "FSMRoute",
    "FSMState",
    # Utils
    "NestedCompleterWithMeta",
    "print_subcommand_help",
]
