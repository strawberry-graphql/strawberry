from enum import Enum

import pytest

import strawberry
from strawberry.utils.deprecations import DEPRECATION_MESSAGES


@strawberry.type
class A:
    a: int


@strawberry.enum
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def test_type_definition_is_aliased():
    with pytest.warns(match=DEPRECATION_MESSAGES._TYPE_DEFINITION):
        assert A.__strawberry_definition__ is A._type_definition


def test_get_warns():
    with pytest.warns(match=DEPRECATION_MESSAGES._TYPE_DEFINITION):
        assert A._type_definition.fields[0]


def test_can_import_type_definition():
    from strawberry.types.base import StrawberryObjectDefinition, TypeDefinition

    assert TypeDefinition
    assert TypeDefinition is StrawberryObjectDefinition


def test_enum_definition_is_aliased():
    with pytest.warns(match=DEPRECATION_MESSAGES._ENUM_DEFINITION):
        assert Color.__strawberry_definition__ is Color._enum_definition


def test_enum_get_warns():
    with pytest.warns(match=DEPRECATION_MESSAGES._ENUM_DEFINITION):
        assert Color._enum_definition.name == "Color"


def test_can_import_enum_definition():
    from strawberry.types.enum import EnumDefinition, StrawberryEnumDefinition

    assert EnumDefinition
    assert EnumDefinition is StrawberryEnumDefinition
