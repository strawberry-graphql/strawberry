import sys
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class TypeC:
    name: str


@strawberry.type
class Edge(Generic[T]):
    @strawberry.field
    def node(self) -> T:  # type: ignore
        ...


@strawberry.type
class Query:
    type_a: Edge[TypeC]
    type_b: Edge[Annotated["TypeC", strawberry.lazy("tests.schema.test_lazy.type_c")]]


if __name__ == "__main__":
    schema = strawberry.Schema(query=Query)
    sys.stdout.write(f"{schema.as_str()}\n")
