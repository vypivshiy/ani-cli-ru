from typing import List, Any, Optional, Iterable, Union

from textual.validation import Validator, ValidationResult

SLICE_OR_SEQUENCE = Union[Iterable[int], int]


class NumberPeekValidator(Validator):
    """validate index in list_input sequence to next rule:

    # validate rule:

    - accept human-like index: starts with 1, ends to len(lst_items)
    - numbers should be in range 0 < NUM <= len(lst_items)
    # accepts:

    - positive numbers
    - slices
    - sequence of positive numbers separated by whitespace

    # Example:

    lst = list(range(10))
    validator = NumberPeekValidator(lst)
    validator.validate('1') OK
    validator.validate('0') FAIL

    validator.validate('1-2') OK
    validator.validate('1-10') OK
    validator.validate('1-12') FAIL

    validator.validate('1 2 3 4') OK
    validator.validate('1 2 3 11 4') FAIL
    """
    def __init__(self, lst_items: List[Any]):
        super().__init__()
        self._len = len(lst_items)

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

    def parse(self, value: str) -> Optional[SLICE_OR_SEQUENCE]:
        # reminder: index input for view starts from 1
        value = value.strip()
        if not value:
            return

        if self._is_digit(value):
            value = int(value)
            if self._is_positive(value) and self._is_valid_index(value):
                return value - 1

        elif self._is_slice(value):
            start, end = [int(i) for i in value.split('-')]
            start_result = self._is_positive(start) and self._is_valid_index(start)
            end_result = self._is_positive(end) and self._is_valid_index(end)

            if start_result and end_result:
                return range(start-1, end)

        elif self._is_sep_value(value):
            values = [int(i) for i in value.split() if i]
            if all(self._is_positive(i) and self._is_valid_index(i) for i in values):
                return [i - 1 for i in values]
        return

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
            return self.failure('Value should be a bigger than zero')
        return self.success()


if __name__ == '__main__':
    print(NumberPeekValidator(list(range(20))).parse('1-5'))