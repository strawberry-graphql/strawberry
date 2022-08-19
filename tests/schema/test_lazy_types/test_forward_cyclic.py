import textwrap
from typing import List, Optional

import strawberry
from strawberry.lazy_type import LazyType
from strawberry.printer import print_schema


TypeA = LazyType["TypeA"]
TypeB = LazyType["TypeB"]


@strawberry.type
class TypeA:
    list_of_a: Optional[List[TypeA]] = None
    list_of_b: Optional[List[TypeB]] = None

    @strawberry.field()
    def type_a(self) -> TypeA:
        return self

    @strawberry.field()
    def type_b(self) -> TypeB:
        return TypeB()


@strawberry.type
class TypeB:
    list_of_a: Optional[List[TypeA]] = None
    list_of_b: Optional[List[TypeB]] = None

    @strawberry.field()
    def type_a(self) -> TypeA:
        return TypeA

    @strawberry.field()
    def type_b(self) -> TypeB:
        return self


def test_cyclic_lazy():
    @strawberry.type
    class Query:
        a: TypeA
        b: TypeB

    expected = """
        type Query {
          a: TypeA!
          b: TypeB!
        }

        type TypeA {
          listOfA: [TypeA!]
          listOfB: [TypeB!]
          typeA: TypeA!
          typeB: TypeB!
        }

        type TypeB {
          listOfA: [TypeA!]
          listOfB: [TypeB!]
          typeA: TypeA!
          typeB: TypeB!
        }
    """
    schema = strawberry.Schema(Query)

    assert print_schema(schema) == textwrap.dedent(expected).strip()
