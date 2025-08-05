from __future__ import annotations

import textwrap
from typing import Annotated

import strawberry


def test_optional_lazy_type_using_or_operator():
    from tests.schema.test_lazy.type_a import TypeA

    global SomeType, AnotherType

    try:

        @strawberry.type
        class SomeType:
            foo: (
                Annotated[TypeA, strawberry.lazy("tests.schema.test_lazy.type_a")]
                | None
            )

        @strawberry.type
        class AnotherType:
            foo: TypeA | None = None

        @strawberry.type
        class Query:
            some_type: SomeType
            another_type: AnotherType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type AnotherType {
          foo: TypeA
        }

        type Query {
          someType: SomeType!
          anotherType: AnotherType!
        }

        type SomeType {
          foo: TypeA
        }

        type TypeA {
          listOfB: [TypeB!]
          typeB: TypeB!
        }

        type TypeB {
          typeA: TypeA!
          typeAList: [TypeA!]!
          typeCList: [TypeC!]!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del SomeType, AnotherType
