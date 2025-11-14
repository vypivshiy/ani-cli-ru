import re
from typing import List


def parse_selection_mask(s: str, n: int) -> List[bool]:
    """
    Разбирает строку выбора индексов и возвращает булеву маску длиной n.
    Индексация 1-based (от 1 до n).

    Поддерживает:
      - одиночные индексы: '1 3 5'
      - диапазоны: '1-3 5-7'
      - комбинации: '1-3 2 5'
    Ошибки:
      - 0 или числа > n
      - range: a >= b
      - неверный формат

    Пример:
        arr = list(range(10))
        mask = parse_selection_mask("1-3 5", len(arr))
        # mask = [True, True, True, False, True, False, False, False, False, False]
    """
    if not isinstance(s, str):
        msg = "s must be a string"
        raise TypeError(msg)
    if not isinstance(n, int) or n <= 0:
        msg = "n must be positive integer"
        raise ValueError(msg)

    tokens = [t for t in re.split(r"\s+", s.strip()) if t != ""]
    if not tokens:
        return [False] * n

    mask = [False] * n

    for tok in tokens:
        if "-" in tok:
            parts = tok.split("-")
            if len(parts) != 2:  # noqa
                msg = f"Bad token: {tok!r}"
                raise ValueError(msg)
            a_str, b_str = parts
            if not a_str.isdigit() or not b_str.isdigit():
                msg = f"Bad range endpoints: {tok!r}"
                raise ValueError(msg)
            a, b = int(a_str), int(b_str)
            if a < 1 or b < 1 or a > n or b > n:
                msg = f"Range {tok!r} out of bounds (1..{n})"
                raise ValueError(msg)
            if a >= b:
                msg = f"Bad range {tok!r} (start must be < end)"
                raise ValueError(msg)
            for i in range(a - 1, b):  # included
                mask[i] = True
        else:
            if not tok.isdigit():
                msg = f"Bad token: {tok!r}"
                raise ValueError(msg)
            v = int(tok)
            if v < 1 or v > n:
                msg = f"Index {v!r} out of bounds (1..{n})"
                raise ValueError(msg)
            mask[v - 1] = True

    return mask
