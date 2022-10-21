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
