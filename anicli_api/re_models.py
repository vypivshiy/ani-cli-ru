from __future__ import annotations

import re
from typing import Pattern, Optional, Any, Type, Union, AnyStr, Dict, Iterable, Callable


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
                 result_type: Type = str,
                 before_func: Optional[Union[Callable, Dict[str, Callable]]] = None,
                 after_func: Optional[Union[Callable, Dict[str, Callable]]] = None):
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)

        self.name = self._set_name(name)

        self.result_type = result_type
        self.before_func = before_func
        self.after_func = after_func
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
                              func: Optional[Union[Dict[str, Callable], Callable]] = None,
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
        if val := self.before_func_call(key=key, value=value):
            value = val
        value = self._set_type(value)
        if val := self.after_func_call(key=key, value=value):
            value = val
        value = self._init_lambda_function(func=self.after_func, key=key, value=value)
        return value

    def parse(self, text: str):
        raise NotImplementedError

    def before_func_call(self, key: str, value: Any):
        ...

    def after_func_call(self, key: str, value: Any):
        ...

    def _set_type(self, value: Any) -> Type[Any]:
        return self.result_type(value)

    def __repr__(self):
        return f"[{self.__class__.__name__}] type={self.result_type} pattern={self.pattern} " \
               f"{{{self.name}: {self.value}}}"


class ReField(ReBaseField):

    def parse(self, text: str) -> Dict[str, Any]:
        if not (result := self.pattern.search(text)):
            if isinstance(self.default, Iterable):
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
                 result_type: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None):

        if not default:
            default = []

        if not isinstance(default, Iterable):
            raise TypeError

        if not isinstance(default, list):
            default = list(default)

        super().__init__(pattern, name=name, default=default,
                         result_type=result_type, before_func=before_func, after_func=after_func)

    def parse(self, text: str) -> Dict:
        if not (result := self.pattern.findall(text)):
            return {self.name: self.default}
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
                 result_type: Type = str,
                 before_func: Optional[Dict[str, Callable]] = None,
                 after_func: Optional[Dict[str, Callable]] = None):
        if not default:
            default = []

        if not isinstance(default, Iterable):
            raise TypeError

        super().__init__(pattern, name=name, default=default,
                         result_type=result_type, before_func=before_func, after_func=after_func)

    def parse(self, text: str) -> Dict:
        if not self.pattern.search(text):
            return {self.name: self.default}
        if not self.pattern.groupindex:
            raise TypeError
        values = []
        for result in self.pattern.finditer(text):
            rez = result.groupdict()
            for k in rez.keys():
                rez[k] = self._enchant_value(k, rez[k])
            values.append(rez)
        return {self.name: values}


def parse_many(text: str, *re_fields: ReBaseField) -> dict:
    result = {}
    for re_field in re_fields:
        result.update(re_field.parse(text))
    return result


if __name__ == '__main__':
    tst = "foo=123, bar=based 9129 800 1 92"
    f = ReField(r"foo=(?P<digit>\d+)", result_type=int)
    f2 = ReField(r"foo=(\d+)", result_type=float, name="float_digit")

    f3 = ReFieldList(r"(\d+)", result_type=int, name="digit_list",
                     before_func=lambda s: f"{s}0",
                     after_func=lambda s: s * 5)

    f4 = ReFieldListDict(r"(?P<key>\w+)=(?P<value>[\d\w]+)", name="lst_dict",
                         after_func={"value": lambda s: int(s) if s.isdigit() else s.title(),
                                      "key": lambda s: s.upper()})

    f5 = ReField(r"patternnotexist", name="empty")

    print(parse_many(tst, f, f2, f3, f4, f5))
