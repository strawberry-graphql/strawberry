from enum import Enum
from typing import Annotated, Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.enum
class MyEnum(Enum):
    ONE = "ONE"


@strawberry.type
class ValueContainer(Generic[T]):
    value: T


UnionValue = Annotated[
    ValueContainer[int] | ValueContainer[MyEnum],
    strawberry.union("UnionValue"),
]
