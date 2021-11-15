from typing import Generic, NewType, TypeVar

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.schema.config import StrawberryConfig
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.union import StrawberryUnion


T = TypeVar("T")


Enum = EnumDefinition(None, name="Enum", values=[], description=None)  # type: ignore
CustomInt = strawberry.scalar(NewType("CustomInt", int))


@strawberry.type
class TypeA:
    name: str


@strawberry.type
class TypeB:
    age: int


@pytest.mark.parametrize(
    "types,expected_name",
    [
        ([StrawberryList(str)], "StrListExample"),
        ([StrawberryList(StrawberryList(str))], "StrListListExample"),
        ([StrawberryOptional(StrawberryList(str))], "StrListOptionalExample"),
        ([StrawberryList(Enum)], "EnumListExample"),
        ([StrawberryUnion("Union", (TypeA, TypeB))], "UnionExample"),  # type: ignore
        ([TypeA], "TypeAExample"),
        ([CustomInt], "CustomIntExample"),
        ([TypeA, TypeB], "TypeATypeBExample"),
        ([TypeA, LazyType["TypeB", "test_names"]], "TypeATypeBExample"),  # type: ignore
    ],
)
def test_name_generation(types, expected_name):
    config = StrawberryConfig()

    @strawberry.type
    class Example(Generic[T]):
        a: T

    type_definition = Example._type_definition  # type: ignore

    assert config.name_converter.from_generic(type_definition, types) == expected_name
