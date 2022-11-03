from __future__ import annotations

import re
from typing import Pattern, Optional, Any, Type, Union, AnyStr, Dict, Iterable, Callable, List, Generator

T_BEFORE_EXEC = Union[Callable[[str], str], Dict[str, Callable[[str], str]]]
T_AFTER_EXEC = Union[Callable[[Any], Any], Dict[str, Callable[[Any], Any]]]

# TODO write docstring, add tests

__all__ = (
    'ReBaseField',
    'ReField',
    'ReFieldList',
    'ReFieldListDict',
    'parse_many',
)


class ReBaseField:
    """base regex parser and dict converter

    work strategy:
        1. set regex pattern and set name. if pattern not found, return  {name: default} dict

        2. functions convert priority:

        2.1  before_func attr, if set

        2.2  before_func_call method

        2.3 result_type set type (default str)

        2.4 after_func_call method

        2.5 after_func attr, if set

        3. return {name: result}
    """

    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 *,
                 name: Optional[str] = None,
                 default: Optional[Any] = None,
                 type: Type = str,
                 before_exec_type: Optional[T_BEFORE_EXEC] = None,
                 after_exec_type: Optional[T_AFTER_EXEC] = None):
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)

        self.name = self._set_name(name)

        self.result_type = type
        self.before_func = before_exec_type
        self.after_func = after_exec_type
        self.default = default
        self.value = None

    def _set_name(self, name):
        if not name and len(self.pattern.groupindex) > 0:
            return ",".join(self.pattern.groupindex)
        else:
            return name

    @staticmethod
    def _init_lambda_function(*,
                              value: Any,
                              func: Optional[Union[Dict[str, Callable[[Any], Any]], Callable[[Any], Any]]] = None,
                              key: str = "",
                              ) -> Any:
        if func:
            if isinstance(func, dict) and func.get(key):
                if not callable(func.get(key)):
                    raise TypeError
                value = func.get(key)(value)  # type: ignore
            elif callable(func):
                value = func(value)
        return value

    def _enchant_value(self, key: str, value: Any):
        value = self._init_lambda_function(func=self.before_func, key=key, value=value)
        if val := self.before_exec_func_call(key=key, value=value):
            value = val
        value = self._set_type(value)
        if val := self.after_exec_func_call(key=key, value=value):
            value = val
        value = self._init_lambda_function(func=self.after_func, key=key, value=value)
        return value

    def parse(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError

    def parse_values(self, text: str) -> List[Any]:
        rez = []
        for val in self.parse(text).values():
            rez.extend(val) if isinstance(val, List) else rez.append(val)

        return rez

    def before_exec_func_call(self, key: str, value: Any):
        ...

    def after_exec_func_call(self, key: str, value: Any):
        ...

    def _set_type(self, value: Any) -> Type[Any]:
        return self.result_type(value)

    def __repr__(self):
        return f"[{self.__class__.__name__}] type={self.result_type} pattern={self.pattern} " \
               f"{{{self.name}: {self.value}}}"


class ReField(ReBaseField):

    def parse(self, text: str) -> Dict[str, Any]:
        if not (result := self.pattern.search(text)):
            if isinstance(self.default, Iterable) and not isinstance(self.default, str):  # string is iterable
                return dict(zip(self.name.split(","), self.default))
            else:
                return {self.name: self.default}
        elif result and self.pattern.groupindex:
            rez = result.groupdict()
        elif result:
            rez = dict(zip(self.name.split(","), result.groups()))
        else:
            raise RuntimeError
        for k in rez.keys():
            rez[k] = self._enchant_value(key=k, value=rez[k])
        return rez


class ReFieldList(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 *,
                 name: str,
                 default: Optional[Iterable[Any]] = None,
                 type: Type = str,
                 before_exec_type: Optional[Callable] = None,
                 after_exec_type: Optional[Callable] = None):

        if not default:
            default = []

        if not isinstance(default, Iterable):
            raise TypeError

        if not isinstance(default, list):
            default = list(default)

        super().__init__(pattern, name=name, default=default,
                         type=type, before_exec_type=before_exec_type, after_exec_type=after_exec_type)

    def parse(self, text: str) -> Dict[str, List]:
        if not (result := self.pattern.findall(text)):
            return {self.name: self.default}  # type: ignore
        for i, el in enumerate(result):
            el = self._enchant_value("", el)
            result[i] = el
        return {self.name: result}


class ReFieldListDict(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 *,
                 name: str,
                 default: Optional[Iterable[Any]] = None,
                 type: Type = str,
                 before_exec_type: Optional[Dict[str, Callable]] = None,
                 after_exec_type: Optional[Dict[str, Callable]] = None):
        if not default:
            default = []

        if not isinstance(default, Iterable):
            raise TypeError

        super().__init__(pattern, name=name, default=default,
                         type=type, before_exec_type=before_exec_type, after_exec_type=after_exec_type)

    def parse(self, text: str) -> Dict[str, List[Any]]:
        if not self.pattern.search(text):
            return {self.name: self.default}  # type: ignore
        if not self.pattern.groupindex:
            raise TypeError
        values = []
        for result in self.pattern.finditer(text):
            rez = result.groupdict()
            for k in rez.keys():
                rez[k] = self._enchant_value(k, rez[k])
            values.append(rez)
        return {self.name: values}


def parse_many(text: str, *re_fields: ReBaseField) -> dict[str, Any]:
    result = {}
    for re_field in re_fields:
        result.update(re_field.parse(text))
    return result


if __name__ == '__main__':
    tst = "foo=123, bar=based 9129 800 1 92"
    f = ReField(r"foo=(?P<digit>\d+)",  # set key "digit"
                type=int)  # convert result to int
    f2 = ReField(r"foo=(\d+)",  # without pattern.groupindex
                 type=float,  # convert to float
                 name="float_digit")  # set key "float_digit"

    f3 = ReFieldList(r"(\d+)",
                     type=int,  # convert all result to int
                     name="lst_digit",  # name
                     before_exec_type=lambda s: f"{s}0",  # add "0" to match
                     after_exec_type=lambda s: s * 5)  # mul integer result to 5

    f4 = ReFieldListDict(r"(?P<key>\w+)=(?P<value>[\d\w]+)",
                         name="lst_dict",
                         # use lambda functions to result
                         after_exec_type={"value": lambda s: int(s) if s.isdigit() else s.title(),
                                          "key": lambda s: s.upper()})

    f5 = ReField(r"patternnotexist", name="empty")  # default return None
    print(f3.parse_values(tst))
    print(f4.parse_values(tst))
    print(f.parse_values(tst))
    print(parse_many(tst, f, f2, f3, f4, f5))
    # {'digit': 123,
    # 'float_digit': 123.0,
    # 'lst_digit': [6150, 456450, 40000, 50, 4600],
    # 'lst_dict': [{'key': 'FOO', 'value': 123}, {'key': 'BAR', 'value': 'Based'}],
    # 'empty': None}
