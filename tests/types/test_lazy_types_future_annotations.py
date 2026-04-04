from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_a import TypeA
    from tests.schema.test_lazy.type_c import TypeC


def test_optional_lazy_type_using_or_operator():

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


def test_lazy_type_with_type_checking_guard():
    """Basic lazy type using TYPE_CHECKING guard (no runtime import)."""
    global BasicLazyType

    try:

        @strawberry.type
        class BasicLazyType:
            child: Annotated[TypeC, strawberry.lazy("tests.schema.test_lazy.type_c")]

        @strawberry.type
        class Query:
            my_type: BasicLazyType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type BasicLazyType {
          child: TypeC!
        }

        type Query {
          myType: BasicLazyType!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del BasicLazyType


def test_optional_lazy_type_with_type_checking_guard():
    """Optional[Annotated[...]] with TYPE_CHECKING guard."""
    global OptionalLazyType

    try:

        @strawberry.type
        class OptionalLazyType:
            child: Optional[
                Annotated[TypeC, strawberry.lazy("tests.schema.test_lazy.type_c")]
            ] = None

        @strawberry.type
        class Query:
            my_type: OptionalLazyType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type OptionalLazyType {
          child: TypeC
        }

        type Query {
          myType: OptionalLazyType!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del OptionalLazyType


def test_or_none_lazy_type_with_type_checking_guard():
    """Annotated[...] | None with TYPE_CHECKING guard."""
    global OrNoneLazyType

    try:

        @strawberry.type
        class OrNoneLazyType:
            child: (
                Annotated[TypeC, strawberry.lazy("tests.schema.test_lazy.type_c")]
                | None
            ) = None

        @strawberry.type
        class Query:
            my_type: OrNoneLazyType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type OrNoneLazyType {
          child: TypeC
        }

        type Query {
          myType: OrNoneLazyType!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del OrNoneLazyType
