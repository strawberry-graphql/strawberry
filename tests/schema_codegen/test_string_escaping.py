import ast
import textwrap

import pytest

from strawberry.schema_codegen import _string_literal, codegen


def test_description_with_both_quotes():
    schema = '''
    """It's a "Star Wars" species."""
    type Species {
        name: String!
    }
    '''

    expected = textwrap.dedent(
        r"""
        from __future__ import annotations
        import strawberry

        @strawberry.type(description="It's a \"Star Wars\" species.")
        class Species:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_description_with_backslashes():
    schema = r'''
    type Species {
        """Stored under C:\species\new."""
        name: String!
    }
    '''

    expected = textwrap.dedent(
        r"""
        from __future__ import annotations
        import strawberry

        @strawberry.type
        class Species:
            name: str = strawberry.field(description="Stored under C:\\species\\new.")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_multiline_description_with_triple_quotes():
    schema = r'''
    """
    A description that quotes another one:
    \"""Nested description.\"""
    """
    type Species {
        name: String!
    }
    '''

    expected = textwrap.dedent(
        r'''
        from __future__ import annotations
        import strawberry

        @strawberry.type(description="""\
        A description that quotes another one:
        ""\"Nested description.""\"\
        """)
        class Species:
            name: str
        '''
    ).strip()

    assert codegen(schema).strip() == expected


def test_string_default_values():
    schema = r"""
    input SpeciesInput {
        name: String! = "first line\nsecond line"
        quote: String! = "It's \"quoted\""
    }
    """

    expected = textwrap.dedent(
        r"""
        from __future__ import annotations
        import strawberry

        @strawberry.input
        class SpeciesInput:
            name: str = "first line\nsecond line"
            quote: str = "It's \"quoted\""
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_specified_by_url_with_quotes():
    schema = r"""
    scalar LocalDate @specifiedBy(url: "https://example.com/local-date?name=\"local\"&kind='date'")
    """

    expected = textwrap.dedent(
        r"""
        from __future__ import annotations
        import strawberry
        from strawberry.types.scalar import ScalarDefinition
        from typing import NewType

        LocalDate = NewType("LocalDate", object)

        scalar_map: dict[object, ScalarDefinition] = {LocalDate: strawberry.scalar(name="LocalDate", specified_by_url="https://example.com/local-date?name=\"local\"&kind='date'", serialize=lambda v: v, parse_value=lambda v: v)}
        """
    ).strip()

    assert codegen(schema).strip() == expected


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        'with "double" quotes',
        "with 'single' quotes",
        'it\'s "both"',
        "ends with a quote'",
        'ends with a quote"',
        "trailing backslash \\",
        "tab\tand\rcarriage return",
        "unicode é 中文 \u2028 separator",
        "first line\nsecond line",
        'multiline with """triple""" quotes\n""""',
        "multiline ending with a backslash \\\n\\",
        "\nstarts and ends with a newline\n",
        'multiline ending with a quote\n"',
    ],
)
@pytest.mark.parametrize("allow_triple_quotes", [True, False])
def test_string_literals_round_trip(value: str, allow_triple_quotes: bool):
    literal = _string_literal(value, allow_triple_quotes=allow_triple_quotes)

    assert ast.literal_eval(literal.value) == value
