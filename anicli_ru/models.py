"""Dataclass regular expressions Parser
Example:
    import re
    class TestModel(BaseModel):
         __REGEX__ = (ReField(r"(\d+)", type_=float, name="digit"),
                      ReFieldList(r"t", type_=str, name="t_lst", after_func=lambda s: f"{s}est"))
         digit: int
         t_lst: list[str]
     sample_test = "test 123 fooobarbaz"
     data = TestModel(sample_test)
     assert data.dict() == {"digit": 123.0, "t_lst": ["test", "test"]}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern, Optional, Any, Type, Callable, Tuple, Union, AnyStr, Match

__all__ = ('BaseModel',
           'ReField',
           'ReFieldList'
           )


@dataclass(init=False)
class ReBaseField:
    """base field class"""

    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 *,
                 name: str = "",
                 type_: Type = str,
                 default: Any = None,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None):
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)
        self.type_ = type_
        self.before_func = before_func
        self.after_func = after_func
        self.name = self._set_name(name)
        self.value: Optional[Any] = None
        self.default = default

    def _set_name(self, name):
        if not name and len(self.pattern.groupindex) > 0:
            return ",".join(self.pattern.groupindex)
        else:
            return name

    def reparse(self, page: str) -> ReBaseField:
        return self._reparse_class(page=page,
                                   pattern=self.pattern,
                                   type_=self.type_,
                                   before_func=self.before_func,
                                   after_func=self.after_func,
                                   name=self.name,
                                   default=self.default)

    @classmethod
    def _reparse_class(cls, **kwargs):
        return cls(**kwargs)

    def __repr__(self):
        return f"[{self.__class__.__name__}] type={self.type_} pattern={self.pattern} " \
               f"name={self.name} value={self.value}"


class ReField(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 page: str = " ",
                 *,
                 name: str = "",
                 default: Any = None,
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None):
        """Convert regular expression result with pattern.search method to variable and return first founded value

        :param pattern: re.compile expression pattern
        :param page: string text. recreate dataclass with cls.reparse method in BaseModel dataclass
        :param name: name variable. Optional, if regular expression have (?P<name_var>...) expression
        :param default: default value, if regex has not found result
        :param type_: type, were need convert result. Default str
        :param before_func: function that activates BEFORE typecasting
        :param after_func: function that activates AFTER typecasting
        """
        super(ReField, self).__init__(pattern,
                                      name=name,
                                      type_=type_,
                                      default=default,
                                      before_func=before_func,
                                      after_func=after_func)

        if result := self.pattern.search(page):
            # if pattern without (?P<name_var>...) expression
            if self.pattern.groupindex:
                # pattern with (?P<name_var>...) expression
                self._group_dict(result, type_)

            elif not name:
                raise AttributeError("Pattern without (?P<name_var>...) expression must have <name> param")

            else:
                self._group(result, type_)
        else:
            self.value = default

    def _group(self, result: Match, type_: Type) -> None:
        result = result.group()
        if self.before_func:
            result = self.before_func(result)

        self.value = type_(result)

        if self.after_func:
            self.value = self.after_func(self.value)

    def _group_dict(self, result: Match, type_: Type) -> None:
        for k, v in result.groupdict().items():
            if not self.name:
                self.name = k

            if self.before_func:
                v = self.before_func(v)
            self.value = type_(v)

            if self.after_func:
                self.value = self.after_func(self.value)


class ReFieldList(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 page: str = " ",
                 *,
                 default: Tuple[Any, ...] = (),
                 name: str = "",
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None
                 ):
        """Convert regular expression result with pattern.findall method to list variables

        :param pattern: re.compile expression pattern
        :param page: string text. recreate dataclass with cls.reparse method in BaseContentData dataclass
        :param name: name variable.
        :param default: default value, if regex not found result. Default empty list
        :param type_: type, were need convert element. Default str
        :param before_func: function that activates BEFORE typecasting
        :param after_func: function that activates AFTER typecasting
        """
        super(ReFieldList, self).__init__(pattern,
                                          name=name,
                                          type_=type_,
                                          default=default,
                                          before_func=before_func,
                                          after_func=after_func)

        if result := self.pattern.findall(page):
            if self.before_func:
                self.value = [self.before_func(i) for i in result]

            self.value = [self.type_(i) for i in result]

            if self.after_func:
                self.value = [self.after_func(i) for i in self.value]

        else:
            self.name = name
            self.value = default


class ReFieldListDict(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 page: str = " ",
                 *,
                 name: str = "",
                 default: Tuple[Any, ...] = (),
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None
                 ):
        """Convert regular expression result with pattern.search method to variable and return list of dicts values.
        If pattern has not found values, return defalut value

        :param pattern: regular expression patter
        :param page: text
        :param name: name variables. if pattern without ?P key, need separate names by `,`
        :param default:
        :param type_:
        :param before_func:
        :param after_func:
        """
        super(ReFieldListDict, self).__init__(pattern,
                                              name=name,
                                              type_=type_,
                                              default=default,
                                              before_func=before_func,
                                              after_func=after_func)
        self.value = []

        if result := self.pattern.search(page):
            # if pattern without (?P<name_var>...) expression
            if not result.groupdict():
                if not name:
                    raise AttributeError("Pattern without (?P<name_var>...) expression must have <name> param")

                names = tuple(n.strip() for n in name.split(","))

                for result in self.pattern.finditer(page):
                    result = result.groups()

                    if self.before_func:
                        result = tuple(self.before_func(i) for i in result)

                    result = tuple(type_(i) for i in result)

                    if self.after_func:
                        result = tuple(self.after_func(i) for i in result)

                    self.value.append(dict(zip(names, result)))
            else:
                # pattern with (?P<name_var>...) expression
                for result in self.pattern.finditer(page):
                    result = result.groupdict()
                    for k in result:
                        if self.before_func:
                            result[k] = self.before_func(result[k])

                        result[k] = type_(result[k])

                        if self.after_func:
                            result[k] = self.after_func(result[k])
                    self.value.append(result)


@dataclass(init=False)
class BaseModel:
    __REGEX__: Tuple[ReBaseField, ...]

    def __init__(self, page: str):
        for cls in self.__REGEX__:
            cls = cls.reparse(page)
            setattr(self, cls.name, cls.value)

    def dict(self):
        return {k: getattr(self, k) for k in self.__annotations__ if not k.startswith("__") and not k.endswith("__")}
