import json
from typing import Any

import pytest

from strawberry.schema_codegen import codegen

STRINGS = [
    pytest.param("plain", id="plain"),
    pytest.param('with "double" quotes', id="double-quotes"),
    pytest.param("with 'single' quotes", id="single-quotes"),
    pytest.param('it\'s "both"', id="both-quotes"),
    pytest.param("ends with a quote'", id="trailing-single-quote"),
    pytest.param('ends with a quote"', id="trailing-double-quote"),
    pytest.param("a\\b and \\n", id="backslashes"),
    pytest.param("trailing backslash \\", id="trailing-backslash"),
    pytest.param("tab\tand\rcarriage return", id="control-characters"),
    pytest.param("unicode é 中文 \u2028 separator", id="unicode"),
    pytest.param("' + str(1 / 0) + '\"", id="expression-after-quote"),
    pytest.param("first line\nsecond line", id="multiline"),
    pytest.param(
        'multiline with """triple""" quotes\n""""', id="multiline-triple-quotes"
    ),
    pytest.param("multiline ending with a backslash \\\n\\", id="multiline-backslash"),
]


def _execute(code: str) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(compile(code, "<generated>", "exec"), namespace)  # noqa: S102
    return namespace


def _expected(value: str) -> str:
    # Multi-line descriptions are written as triple-quoted strings that start
    # and end with a newline.
    return f"\n{value}\n" if "\n" in value else value


@pytest.mark.parametrize("value", STRINGS)
def test_descriptions_are_escaped(value: str):
    schema = f"""
    {json.dumps(value)}
    type Example {{
        {json.dumps(value)}
        name: String!
    }}
    """

    namespace = _execute(codegen(schema))
    definition = namespace["Example"].__strawberry_definition__

    assert definition.description == _expected(value)
    assert definition.fields[0].description == _expected(value)


@pytest.mark.parametrize("value", STRINGS)
def test_string_default_values_are_escaped(value: str):
    schema = f"""
    input ExampleInput {{
        name: String! = {json.dumps(value)}
    }}
    """

    namespace = _execute(codegen(schema))

    assert namespace["ExampleInput"]().name == value


@pytest.mark.parametrize("value", STRINGS)
def test_specified_by_url_is_escaped(value: str):
    schema = f"""
    scalar Example @specifiedBy(url: {json.dumps(value)})
    """

    namespace = _execute(codegen(schema))
    definition = namespace["Example"]._scalar_definition

    assert definition.specified_by_url == _expected(value)
