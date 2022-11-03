from typing import Tuple

import pytest

from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, ReBaseField, parse_many


@pytest.mark.parametrize("field,result", [
    (ReField(r"digit=(?P<digit>\d+)"), {"digit": "1000"}),
    (ReField(r"digit=(?P<digit>\d+)",
             type=int), {"digit": 1000}),
    (ReField(r"digit=(?P<digit>\d+)",
             type=float), {"digit": 1000.0}),
    (ReField(r"digit=(\d+)",
             name="integer"), {"integer": "1000"}),
    (ReField(r"digit=(?P<digit>\d+)",
             type=int,
             after_exec_type=lambda i: i + 10), {"digit": 1010}),
    (ReField(r"digit=(?P<digit>\d+)",
             before_exec_type=lambda s: f"{s}99",
             after_exec_type=lambda b: b.encode()), {"digit": b'100099'}),
    (ReField("failed_pattern", name='failed', default='Not found=('), {'failed': 'Not found=('})

])
def test_re_field(field: ReField, result):
    text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et 
    dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
    digit=1000
    commodo consequat."""
    assert field.parse(text) == result


@pytest.mark.parametrize("field,result", [
    (ReFieldList(r"\s(\w+),",
                 name="words"), {'words': ['amet', 'elit']},
     ),
    (ReFieldList(r"\s(\w+),",
                 name="words", after_exec_type=lambda w: w.upper()), {'words': ['AMET', 'ELIT']},
     ),
    (ReFieldList(r"s..",
                 name="words",
                 before_exec_type=lambda s: s.title(),
                 after_exec_type=lambda s: f"cast: {s}!"), {'words': ['cast: Sum!',
                                                                      'cast: Sit!',
                                                                      'cast: Sec!',
                                                                      'cast: Sci!',
                                                                      'cast: Sed!',
                                                                      'cast: Smo!']},
     ),
    (ReFieldList(r"failed_pattern",
                 name="fail", default=["fail", False, (1, 2, 3)]), {"fail": ["fail", False, (1, 2, 3)]}
     )
])
def test_re_field_list(field: ReFieldList, result):
    text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et 
    dolore magna aliqua."""
    assert field.parse(text) == result


@pytest.mark.parametrize('field,result', [
    (ReFieldListDict(r"(?P<t_word>\w{3}) (?P<end>\w+),",
                     name="Twords"),
     {'Twords': [
         {'t_word': 'sit', 'end': 'amet'},
         {'t_word': 'ing', 'end': 'elit'}
     ]}),
    (ReFieldListDict(r"(?P<t_word>\w{3}) (?P<end>\w+),",
                     name="Twords",
                     before_exec_type={"t_word": lambda k: f"{k}o",
                                       "end": lambda s: f"{s}_ger"},
                     after_exec_type={"t_word": lambda k: len(k),
                                      "end": lambda s: s.title()}
                     ),
     {'Twords': [
         {'t_word': 4, 'end': 'Amet_ger'},
         {'t_word': 4, 'end': 'Elit_ger'}
     ]}),
    (ReFieldListDict(r'failed_pattern', name="fail", default=[{"fail": "fail"}]), {"fail": [{"fail": "fail"}]})
])
def test_re_field_list_dict(field: ReFieldListDict, result):
    text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et 
    dolore magna aliqua."""
    print(field.parse(text))
    assert field.parse(text) == result


# TODO add more tests cases
def test_parse_many():
    text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."""
    result = parse_many(text,
                        ReField(r"fail_Lorem", name="lorem", default="Lorem"),
                        ReFieldList(r"\s(\w{3})\s", name="t_words"),
                        ReFieldListDict(r'\s(?P<d_word>\w{2})\s(?P<word>\w+)', name="lst_dict"))
    assert result == {'lorem': 'Lorem',
                      't_words': ['sit', 'sed'],
                      'lst_dict': [
                          {'d_word': 'do', 'word': 'eiusmod'},
                          {'d_word': 'ut', 'word': 'labore'},
                          {'d_word': 'et', 'word': 'dolore'}
                      ]}
