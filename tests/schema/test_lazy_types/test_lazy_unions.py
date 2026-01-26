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

# New syntax unions (without explicit types= argument) - for issue #4066
NewSyntaxUnion = Annotated[TypeA | TypeB, strawberry.union("NewSyntaxUnion")]
NewSyntaxUnionTyping = Annotated[
    Union[TypeA, TypeB], strawberry.union("NewSyntaxUnionTyping")
]


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


def test_lazy_union_new_syntax_pipe():
    """Test lazy reference to a union defined with the new pipe syntax.

    This tests the fix for issue #4066 where lazy unions using the new syntax
    (without types= argument) would fail with "must define one or more member types".
    """

    @strawberry.type
    class Query:
        item: Annotated[
            "NewSyntaxUnion",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        union NewSyntaxUnion = TypeA | TypeB

        type Query {
          item: NewSyntaxUnion!
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


def test_lazy_union_new_syntax_typing_union():
    """Test lazy reference to a union defined with typing.Union syntax."""

    @strawberry.type
    class Query:
        item: Annotated[
            "NewSyntaxUnionTyping",
            strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions"),
        ]

    expected = """
        union NewSyntaxUnionTyping = TypeA | TypeB

        type Query {
          item: NewSyntaxUnionTyping!
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
