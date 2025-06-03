from enum import Enum
import sys
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.enum
class MyEnum(Enum):
    ONE = "ONE"


@strawberry.type
class ValueContainer(Generic[T]):
    value: T


UnionValue = strawberry.union(
    "UnionValue",
    types=(
        ValueContainer[int],
        ValueContainer[MyEnum],
    ),
)
