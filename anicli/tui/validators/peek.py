from typing import List, Any

from textual.validation import Validator, ValidationResult


class InputPeekValidator(Validator):
    def __init__(self, lst_items: List[Any]):
        super().__init__()
        self._items = lst_items
        self._len = len(lst_items)

    @staticmethod
    def _is_digit(value: str):
        return value.isdigit()

    @staticmethod
    def _is_slice(value: str):
        if len(value.split("-")) == 2:
            start, end = value.split("-")
            return start.isdigit() and end.isdigit()
        return False

    @staticmethod
    def _is_positive(value: int):
        return value > 0

    @staticmethod
    def _is_sep_value(value: str):
        return all(i.isdigit() for i in value.split())

    def _is_valid_index(self, value: int):
        return value <= self._len

    def validate(self, value: str) -> ValidationResult:
        if self._is_digit(value):
            return self._validate_digit(value)
        elif self._is_slice(value):
            return self._validate_slice(value)
        elif self._is_sep_value(value):
            values = [int(i) for i in value.split()]
            if all(self._is_valid_index(i) for i in values):
                return self.success()
        return self.failure('Value should be a positive integer, slice (1-3) or sequence digits "1 2"')

    def _validate_sequence(self, value: str) -> ValidationResult:
        values = [int(i) for i in value.split()]
        if all(self._is_valid_index(i) for i in values):
            return self.success()
        return self.failure('Wrong sequence syntax')

    def _validate_slice(self, value: str) -> ValidationResult:
        start, end = (int(i) for i in value.split("-"))
        if start >= end:
            return self.failure(f'Wrong slice argument {start}>={end}')

        start_result = self._is_positive(start) and self._is_valid_index(start)
        end_result = self._is_positive(end) and self._is_valid_index(end)

        if start_result and end_result:
            return self.success()
        return self.failure('Wrong slice syntax')

    def _validate_digit(self, value: str) -> ValidationResult:
        value = int(value)
        if not self._is_positive(value):
            return self.failure('value should be a bigger than zero')
        return self.success()
