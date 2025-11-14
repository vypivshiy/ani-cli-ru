"""Custom completers with meta information support"""

from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

if TYPE_CHECKING:
    from .application import Application
    from .types import CommandRoute

_LEN_META_COMPLETER_ITEM = 2


class NestedCompleterWithMeta(Completer):
    """Nested completer that supports meta descriptions using _meta key"""

    def __init__(self, options: Dict[str, Any]):
        self.options = options

    def _resolve_dynamic(self, node):
        """Resolve dynamic completions stored in node['_completions']."""
        if not isinstance(node, dict) or "_completions" not in node:
            return None

        dyn = node["_completions"]
        try:
            dyn_res = dyn() if callable(dyn) else dyn
        except Exception:
            return None

        if isinstance(dyn_res, dict):
            return dict(dyn_res)
        elif isinstance(dyn_res, (list, tuple, set)):
            return {str(x): None for x in dyn_res}
        else:
            return None

    def get_completions(
        self,
        document: Document,
        complete_event: Any,  # noqa: ARG002 (ptk API)
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # Split by spaces, preserving structure
        words = text.split(" ")

        # Handle empty input
        if not text or text == "":
            current_word = ""
            words = []
        else:
            # Get the last word being typed
            current_word = words[-1] if words else ""
            # Remove the current word from the path
            words = words[:-1] if len(words) > 1 else []

        current_options = self.options

        # Navigate through the tree using completed words
        for token in words:
            if not token:  # Skip empty tokens
                continue
            if not isinstance(current_options, dict):
                return
            if token in current_options:
                next_node = current_options[token]
                if isinstance(next_node, dict):
                    current_options = next_node
                else:
                    return
            else:
                # If token not found, no completions
                return

        # Merge static and dynamic completions
        merged_options = None
        if isinstance(current_options, dict):
            dyn = self._resolve_dynamic(current_options)
            if dyn is not None:
                # Merge static (non-magic keys) with dynamic
                merged_options = {k: v for k, v in current_options.items() if not k.startswith("_")}
                for k, v in dyn.items():
                    if k not in merged_options:
                        merged_options[k] = v
            else:
                # Only static keys
                merged_options = {k: v for k, v in current_options.items() if not k.startswith("_")}
        else:
            return

        # Yield completions that match the current word
        for key, value in merged_options.items():
            if not key:
                continue
            if key.startswith(current_word):
                meta = None
                if isinstance(value, dict):
                    meta = value.get("_meta", "")
                elif isinstance(value, str):
                    meta = value
                yield Completion(text=key, start_position=-len(current_word), display_meta=meta)

    @classmethod
    def from_nested_dict(cls, options: Dict[str, Any]) -> "NestedCompleterWithMeta":
        return cls(options)


class SubCommandCompleter(Completer):
    """
    Completer for commands with sub_commands.

    Strategy:
    1. First level: show sub-command keys
    2. After selecting sub-command: delegate to that sub-command's completer
    """

    def __init__(self, route: "CommandRoute"):
        self.route = route

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Handle completions for sub-commands:
        - If no words yet, show sub-command keys
        - If first word matches sub-command, delegate to its completer
        """
        text = document.text_before_cursor
        words = text.split()

        # Case 1: Empty or completing first word -> show sub-command keys
        if not words or (len(words) == 1 and not text.endswith(" ")):
            current_word = words[0] if words else ""

            for sub_cmd in self.route.sub_commands:
                if sub_cmd.key.startswith(current_word):
                    yield Completion(text=sub_cmd.key, start_position=-len(current_word), display_meta=sub_cmd.help)

                # Also check aliases
                for alias in sub_cmd.aliases:
                    if alias.startswith(current_word):
                        yield Completion(
                            text=alias,
                            start_position=-len(current_word),
                            display_meta=f"-> {sub_cmd.key}: {sub_cmd.help}",
                        )

        # Case 2: First word is complete, delegate to sub-command's completer
        else:
            first_word = words[0]

            # Find matching sub-command
            matching_sub_cmd = None
            for sub_cmd in self.route.sub_commands:
                if sub_cmd.key == first_word or first_word in sub_cmd.aliases:
                    matching_sub_cmd = sub_cmd
                    break

            if matching_sub_cmd:
                # Check if this sub-command has nested sub-commands
                if matching_sub_cmd.sub_commands:
                    # Recurse with SubCommandCompleter
                    nested_completer = SubCommandCompleter(matching_sub_cmd)
                    # Remove first word from document
                    remaining_text = text[len(first_word) :].lstrip()
                    nested_doc = Document(remaining_text, len(remaining_text))

                    for completion in nested_completer.get_completions(nested_doc, complete_event):
                        yield completion

                # If has a completer, delegate to it
                elif matching_sub_cmd.completer:
                    # Remove first word from document
                    remaining_text = text[len(first_word) :].lstrip()
                    nested_doc = Document(remaining_text, len(remaining_text))

                    for completion in matching_sub_cmd.completer.get_completions(nested_doc, complete_event):
                        yield completion


class ContextualCompleter(Completer):
    """Completer that shows only relevant completions based on context"""

    def __init__(self, app: "Application"):
        self.app = app

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor or ""

        # If FSM is active → FSM-specific completions
        current_fsm = self.app.current_fsm
        if current_fsm is not None:
            # Navigation tokens always available in FSM
            if current_fsm.current_state:
                state_name = current_fsm.current_state.name
                words = text_before_cursor.split()
                prefix = words[0] if words else text_before_cursor
                completions = current_fsm.get_dynamic_completions(state_name, prefix)
                for item in completions:
                    if isinstance(item, Completion):
                        yield item
                    elif isinstance(item, str):
                        yield Completion(item, start_position=-len(prefix))
                    elif isinstance(item, (list, tuple)) and len(item) >= 1:
                        txt = str(item[0])
                        meta = str(item[1]) if len(item) > 1 else ""
                        yield Completion(txt, start_position=-len(prefix), display_meta=meta)

        # Global completions
        # Check if we're completing a command or its arguments
        words = text_before_cursor.split()

        if not words or (len(words) == 1 and not text_before_cursor.endswith(" ")):
            # Completing command name
            prefix = words[0] if words else ""

            # ONLY commands and builtins — NO FSM ROUTES!
            for key, cmd in self.app.command_manager.commands.items():
                if key.startswith(prefix):
                    yield Completion(key, start_position=-len(prefix), display_meta=cmd.help)

            for alias, cmd_key in self.app.command_manager._command_aliases.items():
                if alias.startswith(prefix):
                    cmd = self.app.command_manager.commands.get(cmd_key)
                    meta = f"→ {cmd_key}"
                    if cmd:
                        meta = f"{meta}: {cmd.help}"
                    yield Completion(alias, start_position=-len(prefix), display_meta=meta)
        else:
            # Completing command arguments - delegate to command's completer or sub_commands
            cmd_name = words[0]
            cmd = self.app.command_manager.get_command(cmd_name)

            if cmd:
                # Check if command has sub_commands (priority over completer)
                if cmd.sub_commands:
                    # Use SubCommandCompleter for nested structure
                    sub_completer = SubCommandCompleter(cmd)
                    args_text = text_before_cursor[len(cmd_name) :].lstrip()
                    args_doc = Document(args_text, len(args_text))

                    for completion in sub_completer.get_completions(args_doc, complete_event):
                        yield completion
                elif cmd.completer:
                    # Use the command's completer for arguments
                    # Split the remaining text to handle multiple arguments
                    remaining_text = text_before_cursor[len(cmd_name) :].lstrip()
                    remaining_words = remaining_text.split()

                    # Check if we have arguments and how many
                    if len(remaining_words) == 0:
                        # No arguments yet - show all completions
                        args_doc = Document("", 0)  # Empty document to get all completions
                        for completion in cmd.completer.get_completions(args_doc, complete_event):
                            yield completion
                    elif len(remaining_words) == 1:
                        # One argument - check if it ends with space (meaning we want all options)
                        # or if it's a partial word that needs completion
                        last_word = remaining_words[0]
                        if text_before_cursor.endswith(" "):
                            # Check if this command has a static completer with specific options
                            # For commands with WordCompleter, we should check if the first argument
                            # is already a valid option before showing all options again
                            # We need to collect all possible completions to check against them
                            all_completions = list(cmd.completer.get_completions(Document("", 0), complete_event))
                            valid_options = [comp.text for comp in all_completions]

                            if last_word in valid_options:
                                # The first argument is already a valid option, don't show the options again
                                # Instead, the user likely wants to type the rest of their prompt
                                # So we don't yield any completions in this case
                                pass
                            else:
                                # The word is not a valid option, show all completions for selection
                                args_doc = Document("", 0)  # Empty document to get all completions
                                for completion in cmd.completer.get_completions(args_doc, complete_event):
                                    yield completion
                        else:
                            # One argument partially typed, show matching completions
                            # Calculate the start position to replace the partial word
                            start_pos = -len(last_word)
                            args_doc = Document(last_word, len(last_word))
                            for completion in cmd.completer.get_completions(args_doc, complete_event):
                                # Adjust the start position to properly replace the word
                                yield Completion(
                                    text=completion.text,
                                    start_position=start_pos,
                                    display_meta=getattr(completion, "display_meta", ""),
                                )
                    else:
                        # Multiple arguments - only complete the last one if it's partial
                        last_word = remaining_words[-1]
                        if text_before_cursor.endswith(" "):
                            # The user typed "cmd sub_cmd1 sub_cmd2 " - show all completions for sub_cmd2 position
                            args_doc = Document("", 0)  # Empty document to get all completions
                            for completion in cmd.completer.get_completions(args_doc, complete_event):
                                yield Completion(
                                    text=completion.text,
                                    start_position=-len(last_word),  # Replace the current word
                                    display_meta=getattr(completion, "display_meta", ""),
                                )
                        else:
                            # Multiple arguments, last one is partial - complete it
                            # Calculate the start position to replace the last partial word
                            start_pos = -len(last_word)
                            args_doc = Document(last_word, len(last_word))
                            completions = list(cmd.completer.get_completions(args_doc, complete_event))

                            # Only show completions if the last word is not an exact match
                            exact_match = any(comp.text == last_word for comp in completions)
                            if not exact_match:
                                for completion in completions:
                                    yield Completion(
                                        text=completion.text,
                                        start_position=start_pos,
                                        display_meta=getattr(completion, "display_meta", ""),
                                    )
                            # Note: We removed the else block that was showing
                            # all completions when there's an exact match
                            # This was causing duplication when the user had already typed a complete option


class HybridFSMCompleter(Completer):
    """Completer that combines static completer (from decorator) and dynamic completions from FSM"""

    def __init__(self, app: "Application", static_completer: Optional[Completer] = None):
        self.app = app
        self.static_completer = static_completer

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        current_fsm = self.app.current_fsm
        current_text = document.text_before_cursor

        all_completions = []

        # 1. dynamic completions from FSM
        if current_fsm and current_fsm.current_state:
            state_name = current_fsm.current_state.name
            dynamic_data = current_fsm.get_dynamic_completions(state_name, current_text)
            if dynamic_data:
                for item in dynamic_data:
                    if isinstance(item, str):
                        all_completions.append(Completion(item, start_position=-len(current_text)))
                    elif isinstance(item, (tuple, list)) and len(item) >= _LEN_META_COMPLETER_ITEM:
                        all_completions.append(
                            Completion(text=item[0], start_position=-len(current_text), display_meta=item[1])
                        )
                    elif isinstance(item, dict):
                        all_completions.append(
                            Completion(
                                text=item.get("text", ""),
                                start_position=-len(current_text),
                                display_meta=item.get("meta", ""),
                            )
                        )

        # 2. static completer from decorator route
        if self.static_completer:
            static_completions = list(self.static_completer.get_completions(document, complete_event))
            # Filter duplicates
            static_texts = {comp.text for comp in all_completions}
            for comp in static_completions:
                if comp.text not in static_texts:
                    all_completions.append(comp)

        # sort and return
        # all_completions.sort(key=lambda x: x.text)
        return all_completions
