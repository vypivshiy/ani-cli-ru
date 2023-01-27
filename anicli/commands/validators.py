from prompt_toolkit.completion import WordCompleter

from typing import Any, Dict, List, Optional, Iterable, Sequence

from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError


class EnumerateValidator(Validator):
    SLICE_ERR = 'Invalid slice. Should be in range {}...{} or {} commands'
    INDEX_ERR = 'Invalid index. Should be in range {}...{} or {} commands'
    INPUT_ERR = 'Invalid input. Should be in range {}...{} or {} commands'

    def __init__(self,
                 choices: Sequence,
                 allowed_commands: Optional[Iterable[str]] = None,
                 *,
                 allow_slice: bool = False,
                 slice_char: str = "-"):
        self.choices = choices
        self.allow_slice = allow_slice
        self.allowed_commands = set(allowed_commands) if allowed_commands else set()
        self.slice_char = slice_char

    def _is_valid_index(self, index: int) -> bool:
        return index in range(len(self.choices))

    def _is_valid_slice(self, start: int, stop: int) -> bool:
        return start in range(len(self.choices)) and stop in range(len(self.choices)) and start <= stop

    def validate(self, document: Document):
        try:
            input_ = document.text
            # check in allowed commands list
            if input_ in self.allowed_commands:
                pass
            # check slice_char in input
            elif self.allow_slice and self.slice_char in input_:
                start_, end_ = map(int, input_.split(self.slice_char))
                if not self._is_valid_slice(start_, end_):
                    raise ValidationError(
                        message=self.SLICE_ERR.format(0, len(self.choices), self.allowed_commands),
                        cursor_position=len(document.text))
            else:
                # check index
                index_ = int(input_)
                if index_ not in range(len(self.choices)):
                    raise ValidationError(
                        message=self.INDEX_ERR.format(0, len(self.choices)-1, self.allowed_commands),
                        cursor_position=len(document.text))
        except ValueError:
            raise ValidationError(
                message=self.INPUT_ERR.format(0, len(self.choices)-1, self.allowed_commands),
                cursor_position=len(document.text))


def input_to_slice(slice_input: str, *, slice_char: str = "-") -> slice:
    start, stop = map(int, slice_input.split(slice_char))
    return slice(start, stop + 1)


def enumerate_completer(
        results: List[Any],
        *,
        whitelist_commands: Optional[Dict[str, str]] = None) -> WordCompleter:
    words = [str(i) for i in range(len(results))]
    meta_dict = {str(i): str(el) for i, el in enumerate(results)}
    if whitelist_commands:
        words.extend(list(whitelist_commands.keys()))
        meta_dict.update(whitelist_commands)
    return WordCompleter(words=words, meta_dict=meta_dict)


def _number_func(
    digit: str,
    max_len: int,
    whitelist_commands: Optional[Iterable[str]] = None):
    if not whitelist_commands:
        whitelist_commands = []
    return digit.isdigit() and 0 <= int(digit) < max_len or digit in whitelist_commands
