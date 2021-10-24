from enum import Enum, auto
from typing import cast

import pytest

import strawberry
from strawberry.enum import StrawberryEnum
from strawberry.exceptions import NotAnEnum


def test_can_use_enum_directly():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    assert IceCreamFlavour.VANILLA.value == "vanilla"
    assert IceCreamFlavour["STRAWBERRY"].value == "strawberry"


def test_enums_with_auto():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = auto()
        STRAWBERRY = auto()
        CHOCOLATE = auto()

    assert IceCreamFlavour.VANILLA.value == 1
    assert IceCreamFlavour.STRAWBERRY.value == 2
    assert IceCreamFlavour.CHOCOLATE.value == 3


def test_basic_enum():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    definition = cast(StrawberryEnum, IceCreamFlavour)

    assert definition.python_name == "IceCreamFlavour"
    assert definition.graphql_name == "IceCreamFlavour"
    assert definition.description is None

    assert definition.values[0].name == "VANILLA"
    assert definition.values[0].value == "vanilla"

    assert definition.values[1].name == "STRAWBERRY"
    assert definition.values[1].value == "strawberry"

    assert definition.values[2].name == "CHOCOLATE"
    assert definition.values[2].value == "chocolate"


def test_can_pass_name_and_description():
    @strawberry.enum(name="Flavour", description="example")
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    definition = cast(StrawberryEnum, IceCreamFlavour)

    assert definition.python_name == "IceCreamFlavour"
    assert definition.graphql_name == "Flavour"
    assert definition.description == "example"


def test_can_use_enum_as_arguments():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def flavour_available(self, flavour: IceCreamFlavour) -> bool:
            return flavour == IceCreamFlavour.STRAWBERRY

    field = Query._type_definition.fields[0]

    assert field.arguments[0].type
    assert isinstance(field.arguments[0].type, StrawberryEnum)


def test_raises_error_when_using_enum_with_a_not_enum_class():
    expected_error = "strawberry.enum can only be used with subclasses of Enum"
    with pytest.raises(NotAnEnum, match=expected_error):

        @strawberry.enum
        class NormalClass:
            hello = "world"
