from typing import Any, NewType, TypeVar

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.schema.config import StrawberryConfig
from strawberry.type import StrawberryList
from strawberry.union import StrawberryUnion


T = TypeVar("T")


Enum = EnumDefinition(None, name="Enum", values=[], description=None)  # type: ignore
JSON = strawberry.scalar(NewType("JSON", Any))


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
        ([JSON], "ExampleJSON"),
        ([TypeA, TypeB], "ExampleTypeATypeB"),
        ([TypeA, LazyType["TypeB", "test_names"]], "ExampleTypeATypeB"),
    ],
)
def test_name_generation(types, expected_name):
    config = StrawberryConfig()

    assert config.name_converter.get_for_concrete_type("Example", types) == expected_name
