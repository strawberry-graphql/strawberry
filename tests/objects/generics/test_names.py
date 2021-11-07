from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.type import StrawberryList
from strawberry.union import StrawberryUnion


T = TypeVar("T")


Enum = EnumDefinition(None, name="Enum", values=[], description=None)


@strawberry.type
class TypeA:
    name: str


@strawberry.type
class TypeB:
    age: int


@pytest.mark.parametrize(
    "types,expected_name",
    [
        ([StrawberryList(str)], "ExampleListStr"),
        ([StrawberryList(StrawberryList(str))], "ExampleListListStr"),
        ([StrawberryList(Enum)], "ExampleListEnum"),
        ([StrawberryUnion("Union", [TypeA, TypeB])], "ExampleUnion"),
        ([TypeA], "ExampleTypeA"),
        ([TypeA, TypeB], "ExampleTypeATypeB"),
    ],
)
def test_name_generation(types, expected_name):
    @strawberry.type
    class Example(Generic[T]):
        node: T

    definition = Example._type_definition

    assert definition.get_name_from_types(types) == expected_name
