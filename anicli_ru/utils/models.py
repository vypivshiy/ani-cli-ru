import re
from dataclasses import dataclass
from typing import Pattern, Generator, Any, Union, NamedTuple, Type, Callable, Sequence
from html import unescape

__all__ = ('BasePatternModel', "RegexField", "PatternModel")


class RegexField(NamedTuple):
    type: Type
    value: Pattern
    re_func: Callable[[Pattern, str], Any] = re.search


class PatternModel(NamedTuple):
    key: str
    value: Any


@dataclass
class BasePatternModel:
    """
    Base auto regex finder model object

    Example::
    >>> import re
    >>> from anicli_ru.utils import BasePatternModel, RegexField
    >>> class TestModel(BasePatternModel):
    ...     KEYS_IGNORE_UPPERCASE = True # default True
    ...     EMPTY_RESULT_VALUE = "Nani?"  # default None
    ...     test_1: RegexField = RegexField(float, re.compile(r"(\d+)"))
    ...     test_2: RegexField = RegexField(int, re.compile(r"(\d+)"), re.findall)
    ...     test_3: RegexField = RegexField(str, re.compile(r"test"))
    ...     useful_constant: int = 900
    ...     IGNORED_CONSTANT = "SECRET"
    >>> # usage
    >>> text = "10 20 30 40 50 testtest whooo"
    >>> for i in TestModel.parse(text):
    ...     i
    PatternModel(key='test_1', value=10.0)
    PatternModel(key='test_2', value=[10, 20, 30, 40, 50])
    PatternModel(key='test_3', value='test')
    PatternModel(key='useful_constant', value=900)
    >>> TestModel.to_dict(text)
    {'test_1': 10.0, 'test_2': [10, 20, 30, 40, 50], 'test_3': 'test', 'useful_constant': 900}

    """
    KEYS_IGNORE_UPPERCASE: bool = True
    EMPTY_RESULT_VALUE: Any = None

    @classmethod
    def _parse_regexp(cls, text, key) -> Any:
        type_value, regexp, func = cls.__dict__.get(key)  # type: ignore

        if isinstance(regexp, Pattern):
            if val := func(regexp, text):
                if isinstance(val, Sequence):
                    val = [type_value(v) for v in val]
                else:
                    val = type_value(val.group())
            else:
                val = cls.EMPTY_RESULT_VALUE
            return val
        return

    @classmethod
    def parse(cls, text: Union[str, bytes], unescape_text: bool = True) -> Generator[PatternModel, None, None]:
        if isinstance(text, bytes):
            text = text.decode()

        if unescape_text:
            text = unescape(text)

        for key in cls.__annotations__.keys():
            # ignore uppercase flag
            if key == "KEYS_IGNORE_UPPERCASE" or (cls.KEYS_IGNORE_UPPERCASE and key.isupper()):
                continue

            if isinstance(cls.__dict__.get(key), RegexField):
                if val := cls._parse_regexp(text, key):
                    yield PatternModel(key, val)

            else:
                yield PatternModel(key, cls.__dict__.get(key))

    @classmethod
    def to_dict(cls, text: Union[str, bytes], unescape_text: bool = True) -> dict[str, Any]:
        return dict(cls.parse(text, unescape_text))
