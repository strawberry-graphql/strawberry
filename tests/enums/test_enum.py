from enum import Enum

import pytest

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.exceptions import ObjectIsNotAnEnumError


def test_basic_enum():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    definition = IceCreamFlavour._enum_definition

    assert definition.name == "IceCreamFlavour"
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

    definition = IceCreamFlavour._enum_definition

    assert definition.name == "Flavour"
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

    assert isinstance(field.arguments[0].type, EnumDefinition)


def test_raises_error_when_using_enum_with_a_not_enum_class():
    expected_error = "strawberry.enum can only be used with subclasses of Enum"
    with pytest.raises(ObjectIsNotAnEnumError, match=expected_error):

        @strawberry.enum
        class NormalClass:
            hello = "world"


def test_can_deprecate_enum_values():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = strawberry.enum_value("vanilla")
        STRAWBERRY = strawberry.enum_value(
            "strawberry", deprecation_reason="We ran out"
        )
        CHOCOLATE = "chocolate"

    definition = IceCreamFlavour._enum_definition

    assert definition.values[0].name == "VANILLA"
    assert definition.values[0].value == "vanilla"
    assert definition.values[0].deprecation_reason is None

    assert definition.values[1].name == "STRAWBERRY"
    assert definition.values[1].value == "strawberry"
    assert definition.values[1].deprecation_reason == "We ran out"

    assert definition.values[2].name == "CHOCOLATE"
    assert definition.values[2].value == "chocolate"
    assert definition.values[2].deprecation_reason is None


def test_can_describe_enum_values():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = strawberry.enum_value("vanilla")
        STRAWBERRY = strawberry.enum_value(
            "strawberry",
            description="Our favourite",
        )
        CHOCOLATE = "chocolate"

    definition = IceCreamFlavour._enum_definition

    assert definition.values[0].name == "VANILLA"
    assert definition.values[0].value == "vanilla"
    assert definition.values[0].description is None

    assert definition.values[1].name == "STRAWBERRY"
    assert definition.values[1].value == "strawberry"
    assert definition.values[1].description == "Our favourite"

    assert definition.values[2].name == "CHOCOLATE"
    assert definition.values[2].value == "chocolate"
    assert definition.values[2].description is None
