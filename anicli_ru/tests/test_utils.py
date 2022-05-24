from base64 import b64encode
import re

import pytest

from anicli_ru.base import ResultList
from anicli_ru.utils import Agent
from anicli_ru import loader
from anicli_ru.utils import Kodik, Aniboom
from anicli_ru.tests.fixtures.fake_extractor import FakeParser, FakeJsonParser


@pytest.mark.parametrize("url", ["//foobarbaz.com/anime_for_debils_4k.mp4",
                                 "https://foobarbaz.com/anime_for_debils_4k.mp4"])
def test_kodik_decode(url: str):
    url_encode = b64encode(url.encode()).decode()[::-1]
    if not url.startswith("https"):
        assert Kodik.decode(url_encode) == "https:" + url
    else:
        assert Kodik.decode(url_encode) == url


def test_kodik_fake():
    pass


def test_kodik_quality():
    pass


def test_aniboom_fake():
    pass


def test_load_fake_extractor():
    loader.import_extractor("anicli_ru.tests.fixtures.fake_extractor")


def test_fake_extractor_episode():
    pass


def test_fake_extractor_search():
    pass


def test_fake_extractor_ongoing():
    pass


def test_fake_extractor_player():
    pass


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
                                  {"a" : "But who's to judge the right from wrong.",
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


@pytest.mark.parametrize("module", ["math", "urllib3", "json", "csv", "anicli_ru.tests.fixtures.fake_extractor_bad"])
def test_wrong_load_extractor(module: str):
    with pytest.raises(AttributeError, match=f'Module {module} has no class Anime'):
        loader.import_extractor(module)


@pytest.mark.parametrize("module", ["anicli_ru.extractors.123foobarbaz",
                                    "anicli_ru.extractors.__foooooooooooo",
                                    "anicli_ru.extractors._asd12f3gsdfg23",
                                    "why what"])
def test_not_exist_load_extractor(module: str):
    with pytest.raises(ModuleNotFoundError, match=f"Module {module} has not founded"):
        loader.import_extractor(module)


@pytest.mark.parametrize("extractor", list(loader.all_extractors(absolute_directory=True)))
def test_load_extractor(extractor):
    loader.import_extractor(extractor)
    assert True


@pytest.mark.parametrize("agent1,agent2", [(Agent.mobile(), Agent.mobile()),
                                           (Agent.desktop(), Agent.desktop()),
                                           (Agent.random(), Agent.random()),
                                           (Agent.desktop(), Agent.mobile()),
                                           (Agent.random(), Agent.mobile()),
                                           (Agent.random(), Agent.desktop())])
def test_fake_agent(agent1: str, agent2: str):
    assert agent1 != agent2
