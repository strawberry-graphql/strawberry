import sys
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


class Mixin(Generic[T]):
    node: T


@strawberry.type
class TypeD(Mixin[int]):
    name: str


@strawberry.type
class Query:
    type_d_1: TypeD
    type_d: Annotated["TypeD", strawberry.lazy("tests.schema.test_lazy.type_d")]


if __name__ == "__main__":
    schema = strawberry.Schema(query=Query)
    sys.stdout.write(f"{schema.as_str()}\n")
