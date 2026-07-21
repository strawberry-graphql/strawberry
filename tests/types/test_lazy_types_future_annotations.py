from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_a import TypeA
    from tests.schema.test_lazy.type_c import TypeC


# Module-level Annotated alias. With `from __future__ import annotations`,
# field annotations are strings, so a field typed as `LazyTypeC` is resolved
# by name through the module globals. The alias must live here (not inside
# the test) for that lookup to find it.
LazyTypeC = Annotated["TypeC", strawberry.lazy("tests.schema.test_lazy.type_c")]


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


def test_module_level_lazy_alias():
    """Module-level Annotated alias resolves under `from __future__ import annotations`."""
    global AliasedLazyType

    try:

        @strawberry.type
        class AliasedLazyType:
            child: LazyTypeC

        @strawberry.type
        class Query:
            my_type: AliasedLazyType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type AliasedLazyType {
          child: TypeC!
        }

        type Query {
          myType: AliasedLazyType!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del AliasedLazyType


def test_module_level_lazy_alias_in_list():
    """Module-level Annotated alias wrapped in `list[...]` resolves correctly."""
    global AliasedListLazyType

    try:

        @strawberry.type
        class AliasedListLazyType:
            children: list[LazyTypeC]

        @strawberry.type
        class Query:
            my_type: AliasedListLazyType

        schema = strawberry.Schema(query=Query)
        expected = """\
        type AliasedListLazyType {
          children: [TypeC!]!
        }

        type Query {
          myType: AliasedListLazyType!
        }

        type TypeC {
          name: String!
        }
        """
        assert str(schema).strip() == textwrap.dedent(expected).strip()
    finally:
        del AliasedListLazyType
