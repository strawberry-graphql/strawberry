from enum import Enum

import pytest

from typing_extensions import Annotated

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.exceptions import MultipleStrawberryEnumValuesError, NotAnEnum


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


def test_can_pass_value_description():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA: Annotated[
            str, strawberry.enum_value(description="Classic Vanilla")
        ] = "vanilla"
        STRAWBERRY: Annotated[
            str, strawberry.enum_value(description="Sweet Strawberry")
        ] = "strawberry"
        CHOCOLATE: Annotated[
            str, strawberry.enum_value(description="Rich Chocolate")
        ] = "chocolate"

    definition = IceCreamFlavour._enum_definition

    assert definition.values[0].name == "VANILLA"
    assert definition.values[0].value == "vanilla"
    assert definition.values[0].description == "Classic Vanilla"

    assert definition.values[1].name == "STRAWBERRY"
    assert definition.values[1].value == "strawberry"
    assert definition.values[1].description == "Sweet Strawberry"

    assert definition.values[2].name == "CHOCOLATE"
    assert definition.values[2].value == "chocolate"
    assert definition.values[2].description == "Rich Chocolate"


def test_multiple_annotated_enum_values_exception():
    with pytest.raises(MultipleStrawberryEnumValuesError) as error:

        @strawberry.enum
        class IceCreamFlavour(Enum):
            STRAWBERRY: Annotated[
                str,
                strawberry.enum_value(description="Sweet Strawberry"),
                strawberry.enum_value(description="My favourite flavour!"),
            ] = "strawberry"

    assert str(error.value) == (
        "Annotation for enum value `STRAWBERRY` on enum "
        "`IceCreamFlavour` cannot have multiple `strawberry.enum_values`s"
    )


def test_annotated_with_other_information():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        STRAWBERRY: Annotated[str, "some other info"] = "strawberry"

    definition = IceCreamFlavour._enum_definition

    assert definition.name == "IceCreamFlavour"

    assert definition.values[0].name == "STRAWBERRY"
    assert definition.values[0].value == "strawberry"
    assert definition.values[0].description is None


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
    with pytest.raises(NotAnEnum, match=expected_error):

        @strawberry.enum
        class NormalClass:
            hello = "world"
