from typing import Any, Sequence, ClassVar, Set  # noqa

from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator


class NumPromptValidator(Validator):
    """Create validation choice from iterable collection"""

    _ASSIGNED_COMMANDS: ClassVar[Set[str]] = {"..", "~"}  # back prev step  # back main menu

    def __init__(self, items_list: Sequence[Any]):
        self.items_list = items_list
        self.items_len = len(items_list)

    def _is_not_out_of_range(self, text: str) -> bool:
        return text.isdigit() and 0 < int(text) <= self.items_len

    def _in_assigned_commands(self, text: str) -> bool:
        return text in self._ASSIGNED_COMMANDS

    def validate(self, document: Document) -> None:
        text = document.text
        if self._is_not_out_of_range(text):
            return
        elif self._in_assigned_commands(text):
            return
        raise ValidationError(message="Should be digit, or (`..`, `~`)")


class AnimePromptValidator(NumPromptValidator):
    """validator for choice episode state"""

    _ASSIGNED_COMMANDS: ClassVar[Set[str]] = {"..", "~", "info"}  # get title information

    def _is_valid_slice(self, text: str) -> bool:
        text_slice_count = 2

        def is_digits(start_, end_) -> bool:
            return start_.isdigit() and end_.isdigit()

        def is_not_out_of_range(start_: str, end_: str) -> bool:
            return 0 < int(start_) < int(end_) <= self.items_len

        if len(text.split("-")) == text_slice_count:
            start, end = text.split("-")
            if is_digits(start, end) and is_not_out_of_range(start, end):
                return True
            else:
                raise ValidationError(message="Wrong slice range")
        return False

    def validate(self, document: Document) -> None:
        text = document.text
        if self._is_not_out_of_range(text):
            return
        elif self._in_assigned_commands(text):
            return
        elif self._is_valid_slice(text):
            return

        raise ValidationError(message=f"Should be digit, slice (1-{self.items_len}) or (`..`, `~`, `info`)")
