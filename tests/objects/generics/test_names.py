from typing import TypeVar

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.schema.config import StrawberryConfig
from strawberry.type import StrawberryList
from strawberry.union import StrawberryUnion


T = TypeVar("T")


Enum = EnumDefinition(None, name="Enum", values=[], description=None)  # type: ignore


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
        ([TypeA, TypeB], "ExampleTypeATypeB"),
    ],
)
def test_name_generation(types, expected_name):
    config = StrawberryConfig()

    assert config.get_name_from_types("Example", types) == expected_name
