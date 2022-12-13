import textwrap
from typing import TYPE_CHECKING, Generic, TypeVar
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from tests.schema.test_lazy.type_a import TypeA  # noqa


T = TypeVar("T")

TypeAType = Annotated["TypeA", strawberry.lazy("tests.schema.test_lazy.type_a")]


def test_lazy_types_with_generic():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        users: Edge[TypeAType]

    strawberry.Schema(query=Query)


def test_no_generic_type_duplication_with_lazy():
    from tests.schema.test_lazy.type_a import TypeB_abs, TypeB_rel
    from tests.schema.test_lazy.type_b import TypeB

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Query:
        users: Edge[TypeB]
        relatively_lazy_users: Edge[TypeB_rel]
        absolutely_lazy_users: Edge[TypeB_abs]

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Query {
          users: TypeBEdge!
          relativelyLazyUsers: TypeBEdge!
          absolutelyLazyUsers: TypeBEdge!
        }

        type TypeA {
          listOfB: [TypeB!]
          typeB: TypeB!
        }

        type TypeB {
          typeA: TypeA!
        }

        type TypeBEdge {
          node: TypeB!
        }
        """
    ).strip()

    assert str(schema) == expected_schema
