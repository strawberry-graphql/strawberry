from typing import Generic, NewType, TypeVar

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.schema.config import StrawberryConfig
from strawberry.type import StrawberryList
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
        ([StrawberryList(str)], "ExampleListStr"),
        ([StrawberryList(StrawberryList(str))], "ExampleListListStr"),
        ([StrawberryList(Enum)], "ExampleListEnum"),
        ([StrawberryUnion("Union", (TypeA, TypeB))], "ExampleUnion"),  # type: ignore
        ([TypeA], "ExampleTypeA"),
        ([CustomInt], "ExampleCustomInt"),
        ([TypeA, TypeB], "ExampleTypeATypeB"),
        ([TypeA, LazyType["TypeB", "test_names"]], "ExampleTypeATypeB"),  # type: ignore
    ],
)
def test_name_generation(types, expected_name):
    config = StrawberryConfig()

    @strawberry.type
    class Example(Generic[T]):
        a: T

    type_definition = Example._type_definition  # type: ignore

    assert config.name_converter.from_generic(type_definition, types) == expected_name
