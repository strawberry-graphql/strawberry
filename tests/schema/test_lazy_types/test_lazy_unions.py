import textwrap
from typing import Annotated, Union

import strawberry
from strawberry.printer import print_schema


@strawberry.type
class TypeA:
    a: int


@strawberry.type
class TypeB:
    b: int


ABUnion = Annotated[TypeA | TypeB, strawberry.union("ABUnion", types=[TypeA, TypeB])]


TypeALazy = Annotated[
    "TypeA", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions")
]
TypeBLazy = Annotated[
    "TypeB", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions")
]
LazyABUnion = Annotated[
    TypeALazy | TypeBLazy,
    strawberry.union("LazyABUnion", types=[TypeALazy, TypeBLazy]),
]

# New syntax unions (without explicit types= argument) - issue #4066
# These use the recommended migration path from the deprecation warning
NewSyntaxUnion = Annotated[TypeA | TypeB, strawberry.union("NewSyntaxUnion")]
NewSyntaxUnionTyping = Annotated[Union[TypeA, TypeB], strawberry.union("NewSyntaxUnionTyping")]
SingleTypeUnion = Annotated[Union[TypeA], strawberry.union("SingleTypeUnion")]


def test_lazy_union_with_non_lazy_members():
    @strawberry.type
    class Query:
        ab: Annotated[
            "ABUnion", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions")
        ]

    expected = """
        union ABUnion = TypeA | TypeB

        type Query {
          ab: ABUnion!
        }

        type TypeA {
          a: Int!
        }

        type TypeB {
          b: Int!
        }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_lazy_union_with_lazy_members():
    @strawberry.type
    class Query:
        ab: Annotated[
            "LazyABUnion",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        union LazyABUnion = TypeA | TypeB

        type Query {
          ab: LazyABUnion!
        }

        type TypeA {
          a: Int!
        }

        type TypeB {
          b: Int!
        }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_lazy_union_with_new_syntax():
    """Test the new Annotated syntax without explicit types= argument.

    This tests the fix for issue #4066 where lazy unions using the recommended
    new syntax (without types= argument) would fail with:
    "Union type X must define one or more member types."
    """

    @strawberry.type
    class Query:
        ab: Annotated[
            "NewSyntaxUnion",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        union NewSyntaxUnion = TypeA | TypeB

        type Query {
          ab: NewSyntaxUnion!
        }

        type TypeA {
          a: Int!
        }

        type TypeB {
          b: Int!
        }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_lazy_union_with_new_syntax_typing_union():
    """Test the new Annotated syntax using typing.Union instead of pipe operator."""

    @strawberry.type
    class Query:
        ab: Annotated[
            "NewSyntaxUnionTyping",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        union NewSyntaxUnionTyping = TypeA | TypeB

        type Query {
          ab: NewSyntaxUnionTyping!
        }

        type TypeA {
          a: Int!
        }

        type TypeB {
          b: Int!
        }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_lazy_union_with_single_type():
    """Test the new Annotated syntax with a single-type union.

    Single-type unions are a valid use case and should also work with lazy loading.
    """

    @strawberry.type
    class Query:
        ab: Annotated[
            "SingleTypeUnion",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        type Query {
          ab: SingleTypeUnion!
        }

        union SingleTypeUnion = TypeA

        type TypeA {
          a: Int!
        }
    """

    schema = strawberry.Schema(query=Query)
    assert print_schema(schema) == textwrap.dedent(expected).strip()
