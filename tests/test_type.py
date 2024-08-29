import dataclasses
from typing import Optional
from typing_extensions import assert_type

import pytest

import strawberry
from strawberry.types.base import StrawberryObjectDefinition, get_object_definition


def test_get_object_definition():
    @strawberry.type
    class Fruit:
        name: str

    obj_definition = get_object_definition(Fruit)
    assert_type(obj_definition, Optional[StrawberryObjectDefinition])
    assert obj_definition is not None
    assert isinstance(obj_definition, StrawberryObjectDefinition)


def test_get_object_definition_non_strawberry_type():
    @dataclasses.dataclass
    class Fruit:
        name: str

    assert get_object_definition(Fruit) is None

    class OtherFruit: ...

    assert get_object_definition(OtherFruit) is None


def test_get_object_definition_strict():
    @strawberry.type
    class Fruit:
        name: str

    obj_definition = get_object_definition(Fruit, strict=True)
    assert_type(obj_definition, StrawberryObjectDefinition)

    class OtherFruit:
        name: str

    with pytest.raises(
        TypeError,
        match=".* does not have a StrawberryObjectDefinition",
    ):
        get_object_definition(OtherFruit, strict=True)
