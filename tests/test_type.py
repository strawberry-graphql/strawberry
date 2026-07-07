import dataclasses
from typing import Optional
from typing_extensions import assert_type

import pytest

import strawberry
from strawberry.types.base import StrawberryObjectDefinition, get_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.object_type import field


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
        match=r".* does not have a StrawberryObjectDefinition",
    ):
        get_object_definition(OtherFruit, strict=True)


def test_public_decorators_have_dataclass_transform():
    expected = {
        "eq_default": True,
        "order_default": True,
        "kw_only_default": True,
        "frozen_default": False,
        "field_specifiers": (field, StrawberryField),
        "kwargs": {},
    }

    assert strawberry.type.__dataclass_transform__ == expected
    assert strawberry.input.__dataclass_transform__ == expected
    assert strawberry.interface.__dataclass_transform__ == expected
