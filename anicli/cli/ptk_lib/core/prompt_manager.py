"""Prompt message management with dynamic formatting"""

from typing import Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer
from prompt_toolkit.validation import Validator


class PromptManager:
    """Manages the dynamic prompt message shown to the user.

    Supports template formatting like "~/search/{anime}/episode/{ep}".

    Args:
        msg: Default prompt message template
    """

    def __init__(self, msg: str = "~ "):
        self._default_template = msg
        self._template: str = msg  # default prompt template
        self._vars: Dict[str, str] = {}  # variables for .format()
        self._session: Optional[PromptSession] = None

    def reset_prompt_template(self):
        """Reset the prompt template to the default and clear all variables."""
        self.clear_vars()
        self.set_prompt_template(self._default_template)

    def set_prompt_template(self, template: str) -> None:
        """Set the prompt template (e.g., "~/search/{anime} ").

        Args:
            template: The new prompt template string
        """
        self._template = template
        self._update_session_message()

    def update_vars(self, vars_dict: Dict[str, str]) -> None:
        """Update formatting variables (e.g., {"anime": "5"}).

        Args:
            vars_dict: Dictionary of variable names to values for template formatting
        """
        self._vars.update(vars_dict)
        self._update_session_message()

    def clear_vars(self) -> None:
        """Clear all formatting variables."""
        self._vars.clear()
        self._update_session_message()

    def get_current_prompt(self) -> str:
        """Render current prompt using template and variables.

        Returns:
            The formatted prompt string with variables substituted
        """
        try:
            return self._template.format(**self._vars)
        except KeyError as e:
            # fallback if variable missing (e.g., during transition)
            return self._template.replace("{" + str(e) + "}", "<unset>")

    def bind_session(self, session: PromptSession) -> None:
        """Bind to a PromptSession to control its message.

        Args:
            session: The PromptSession to bind to
        """
        self._session = session
        self._update_session_message()

    def _update_session_message(self) -> None:
        """Update the bound PromptSession's message."""
        if self._session is not None:
            self._session.message = self.get_current_prompt()

    def configure_session(
        self,
        *,
        completer: Optional[Completer] = None,
        validator: Optional[Validator] = None,
    ) -> PromptSession:
        """Create or reconfigure a PromptSession with current prompt,
        and optional completer/validator (used in FSM states).

        Args:
            completer: Optional completer for the prompt session
            validator: Optional validator for the prompt session

        Returns:
            Configured PromptSession instance
        """
        session = PromptSession(
            message=self.get_current_prompt(),
            completer=completer,
            validator=validator,
            refresh_interval=0.5,
        )
        self.bind_session(session)
        return session
