import re

import pytest

from anicli_ru.base import BaseAnimeHTTP, ResultList
from tests.fixtures.fake_extractor import FakeParser, FakeJsonParser


def test_animehttp_singleton():
    anime_1, anime_2 = BaseAnimeHTTP(), BaseAnimeHTTP()
    assert anime_1 == anime_2


@pytest.mark.parametrize("html", ["foo=abc\nbar=456\nbaz=789",
                                  "foo=test123\nbar=None\nbaz=100500\ntrash\nbruh bruh brun\n...",
                                  "foo=123 bar=test baz=100500 olololololololololo",
                                  "<some-tag class='kek' foo='test123' bar='O!' baz=15>What?</some-tag>"])
def test_parser(html: str):
    # TODO rewrite that test
    # FakeParser have typed attrs: foo: str, baz: int
    obj = FakeParser.parse(html)
    assert isinstance(obj, ResultList)
    assert isinstance(obj[0], FakeParser)
    assert obj[0].foo == str(re.findall(r"foo=(.*?)", html)[0])
    assert obj[0].baz == int(re.findall(r"baz=(\d+)", html)[0])


@pytest.mark.parametrize("data", [{"foo": "abc", "bar": 456, "baz": 789},
                                  {"foo": "foo", "bar": 9000, "baz": 0,
                                   "a": "MAKING THE MOTHER OF ALL OMELETTES HERE JACK, CAN'T FRET OVER EVERY EGG!"},
                                  {"a": "But who's to judge the right from wrong.",
                                   "b": ["Just like me trying to make history.",
                                         "When our guard is down I think we'll both agree."],
                                   "c": {"foo": "That ViOLECE, breeds ViOLENCE.",
                                         "bar": "But in the end it has to be this way."},
                                   "foo": "^_^",
                                   "bar": 0, "baz": 0}])
def test_parser_json(data: dict):
    # FakeJsonParser have typed attrs: foo, bar and baz
    obj = FakeJsonParser.parse(data)
    assert isinstance(obj, ResultList)
    assert isinstance(obj[0], FakeJsonParser)
    assert obj[0].foo == data.get("foo")
    assert obj[0].bar == data.get("bar")
    assert obj[0].baz == data.get("baz")
