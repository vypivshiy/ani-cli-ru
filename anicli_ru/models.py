"""Dataclass regular expressions Parser
Example:
    >>> import re
    >>> class TestModel(BaseModel):
    >>>     __REGEX__ = (ReField(r"(\d+)", type_=float, name="digit"),
    >>>                  ReFieldList(r"t", type_=str, name="t_lst", after_func=lambda s: f"{s}est"))
    >>>     digit: int
    >>>     t_lst: list[str]
    >>> sample_test = "test 123 fooobarbaz"
    >>> data = TestModel(sample_test)
    >>> assert data.dict() == {"digit": 123.0, "t_lst": ["test", "test"]}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern, Optional, Any, Type, Callable, Tuple, Union, AnyStr

__all__ = ('BaseModel',
           'ReField',
           'ReFieldList')


@dataclass(init=False)
class ReBaseField:
    """base field class"""

    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 *,
                 name: str = "undefined",
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None):
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)
        self.type = type_
        self.before_func = before_func
        self.after_func = after_func
        self.name = name
        self.name = name
        self.value: Optional[Any] = None

    def reparse(self, page: str) -> ReBaseField:
        raise NotImplementedError

    @classmethod
    def _reparse_class(cls, **kwargs):
        raise NotImplementedError


class ReField(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 page: str = " ",
                 *,
                 name: str,
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None):
        """Convert regular expression result with pattern.search method to variable

        :param pattern: re.compile expression pattern
        :param page: string text. recreate dataclass with cls.reparse method in BaseContentData dataclass
        :param name: name variable.
        :param type_: type, were need convert result. Default str
        :param before_func: function that activates BEFORE typecasting
        :param after_func: function that activates AFTER typecasting
        """
        super(ReField, self).__init__(pattern,
                                      name=name,
                                      type_=type_,
                                      before_func=before_func,
                                      after_func=after_func)

        if result := self.pattern.search(page):
            # if pattern without (?P<name_var>...) expression
            if not result.groupdict():
                result = result.group()
                self.name = self.name

                if self.before_func:
                    result = self.before_func(result)

                self.value = type_(result)

                if self.after_func:
                    self.value = self.after_func(self.value)

            else:
                # pattern with (?P<name_var>...) expression
                for k, v in result.groupdict().items():
                    self.name = k if self.name else self.name

                    if self.before_func:
                        v = self.before_func(v)
                    self.value = type_(v)

                    if self.after_func:
                        self.value = self.after_func(self.value)

    def reparse(self, page: str) -> ReField:
        return self._reparse_class(pattern=self.pattern,
                                   type_=self.type,
                                   page=page,
                                   name=self.name,
                                   before_func=self.before_func,
                                   after_func=self.after_func)

    @classmethod
    def _reparse_class(cls, **kwargs) -> ReField:
        return cls(**kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__} {self.type} {self.pattern} {self.name} {self.value}"


class ReFieldList(ReBaseField):
    def __init__(self,
                 pattern: Union[Pattern, AnyStr],
                 page: str = " ",
                 *,
                 name: str,
                 type_: Type = str,
                 before_func: Optional[Callable] = None,
                 after_func: Optional[Callable] = None
                 ):
        """Convert regular expression result with pattern.findall method to list variables

        :param pattern: re.compile expression pattern
        :param page: string text. recreate dataclass with cls.reparse method in BaseContentData dataclass
        :param name: name variable.
        :param type_: type, were need convert element. Default str
        :param before_func: function that activates BEFORE typecasting
        :param after_func: function that activates AFTER typecasting
        """
        super(ReFieldList, self).__init__(pattern,
                                          name=name,
                                          type_=type_,
                                          before_func=before_func,
                                          after_func=after_func)

        if result := self.pattern.findall(page):
            if self.before_func:
                self.value = [self.before_func(i) for i in result]

            self.value = [self.type(i) for i in result]

            if self.after_func:
                self.value = [self.after_func(i) for i in self.value]

        else:
            self.name = name
            self.value = []

    def reparse(self, page: str) -> ReFieldList:
        return self._reparse_class(pattern=self.pattern,
                                   type_=self.type,
                                   page=page,
                                   name=self.name,
                                   before_func=self.before_func,
                                   after_func=self.after_func)

    @classmethod
    def _reparse_class(cls, **kwargs) -> ReFieldList:
        return cls(**kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__} {self.type} {self.pattern} {self.name} {self.value}"


@dataclass(init=False)
class BaseModel:
    __REGEX__: Tuple[ReBaseField, ...]

    def __init__(self, page: str):
        for cls in self.__REGEX__:
            cls = cls.reparse(page)
            setattr(self, cls.name, cls.value)

    def dict(self):
        return {k: getattr(self, k) for k in self.__annotations__ if k != "__REGEX__"}
