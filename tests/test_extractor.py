import pytest

from anicli_ru import loader


FAKE_EXTRACTOR = "tests.fixtures.fake_extractor"
FAKE_WRONG_EXTRACTOR = "tests.fixtures.fake_extractor_bad"


def test_fake_load_extractor():
    loader.import_extractor("tests.fixtures.fake_extractor")


@pytest.mark.parametrize("module", ["math", "urllib", "json", "csv", FAKE_WRONG_EXTRACTOR])
def test_wrong_load_extractor(module: str):
    with pytest.raises(AttributeError):
        loader.import_extractor(module)


@pytest.mark.parametrize("module", ["anicli_ru.extractors.123foobarbaz",
                                    "anicli_ru.extractors.__foooooooooooo",
                                    "anicli_ru.extractors._asd12f3gsdfg23",
                                    "why what"])
def test_not_exist_load_extractor(module: str):
    with pytest.raises(ModuleNotFoundError):
        loader.import_extractor(module)


@pytest.mark.parametrize("extractor", list(loader.all_extractors(absolute_directory=True)))
def test_load_extractor(extractor):
    assert loader.import_extractor(extractor)
