from typing import List, Any

from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError


class NumPromptValidator(Validator):
    def __init__(self, items_list: List[Any]):
        self.items_list = items_list
        self.items_len = len(items_list)

    def validate(self, document: Document) -> None:
        text = document.text
        if text.isdigit() and -1 < int(text) < self.items_len:
            return
        elif text in ("..", "~"):
            return
        raise ValidationError(message="Should be digit, or `..` `~`")


class SliceNumPromptValidator(Validator):
    def __init__(self, items_list: List[Any]):
        self.items_list = items_list
        self.items_len = len(items_list)

    def validate(self, document: Document) -> None:
        text = document.text
        if text.isdigit() and -1 < int(text) < self.items_len:
            return
        elif len(text.split("-")) == 2:
            start, end = text.split("-")
            if start.isdigit() and end.isdigit() and -1 < int(start) < int(end) >= self.items_len:
                return
        elif text in ("..", "~"):
            return
        raise ValidationError(message="Should be digit, or `..` `~` or slice eg 0-2")


class AnimePromptValidator(Validator):
    def __init__(self, items_list: List[Any]):
        self.items_list = items_list
        self.items_len = len(items_list)

    def validate(self, document: Document) -> None:
        text = document.text
        if text.isdigit() and -1 < int(text) < self.items_len:
            return
        elif text in ("..", "~", "info"):
            return
        elif len(text.split("-")) == 2:
            start, end = text.split("-")
            if start.isdigit() and end.isdigit() and -1 < int(start) < int(end) >= self.items_len:
                return
        raise ValidationError(message=f"Should be digit, slice `0-{self.items_len}` or (`..`, `~`, `info`)")
