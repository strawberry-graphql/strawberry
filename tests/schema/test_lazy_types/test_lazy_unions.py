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


ABUnion = Annotated[
    Union[TypeA, TypeB], strawberry.union("ABUnion", types=[TypeA, TypeB])
]


TypeALazy = Annotated[
    "TypeA", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions")
]
TypeBLazy = Annotated[
    "TypeB", strawberry.lazy("tests.schema.test_lazy_types.test_lazy_unions")
]
LazyABUnion = Annotated[
    Union[
        TypeALazy,
        TypeBLazy,
    ],
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
