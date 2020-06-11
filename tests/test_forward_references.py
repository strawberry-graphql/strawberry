from __future__ import annotations

import textwrap

import pytest

import strawberry
from strawberry.printer import print_schema


# Need to investigate this more, see: https://bugs.python.org/issue34776
# Looks like types are returned as strings, so we'd need to find the actual
# class, maybe from the global namespace. Or maybe from our type map


@pytest.mark.xfail(strict=True, reason="Future style annotation are currently broken")
def test_forward_reference():
    @strawberry.type
    class MyType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        me: MyType

    expected_representation = """
    type MyType {
      id: ID!
    }

    type Query {
      me: MyType!
    }
    """

    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()
