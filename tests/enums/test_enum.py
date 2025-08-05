from enum import Enum, IntEnum

import pytest

import strawberry
from strawberry.exceptions import ObjectIsNotAnEnumError
from strawberry.types.base import get_object_definition
from strawberry.types.enum import EnumDefinition


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

    field = Query.__strawberry_definition__.fields[0]

    assert isinstance(field.arguments[0].type, EnumDefinition)


@pytest.mark.raises_strawberry_exception(
    ObjectIsNotAnEnumError,
    match="strawberry.enum can only be used with subclasses of Enum. ",
)
def test_raises_error_when_using_enum_with_a_not_enum_class():
    @strawberry.enum
    class AClass:
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


def test_can_use_enum_values():
    @strawberry.enum
    class TestEnum(Enum):
        A = "A"
        B = strawberry.enum_value("B")
        C = strawberry.enum_value("Coconut", deprecation_reason="We ran out")

    assert TestEnum.B.value == "B"

    assert [x.value for x in TestEnum.__members__.values()] == [
        "A",
        "B",
        "Coconut",
    ]


def test_int_enums():
    @strawberry.enum
    class TestEnum(IntEnum):
        A = 1
        B = 2
        C = 3
        D = strawberry.enum_value(4, description="D")

    assert TestEnum.A.value == 1
    assert TestEnum.B.value == 2
    assert TestEnum.C.value == 3
    assert TestEnum.D.value == 4

    assert [x.value for x in TestEnum.__members__.values()] == [1, 2, 3, 4]


def test_default_enum_implementation() -> None:
    class Foo(Enum):
        BAR = "bar"
        BAZ = "baz"

    @strawberry.type
    class Query:
        @strawberry.field
        def foo(self, foo: Foo) -> Foo:
            return foo

    schema = strawberry.Schema(Query)
    res = schema.execute_sync("{ foo(foo: BAR) }")
    assert not res.errors
    assert res.data
    assert res.data["foo"] == "BAR"


def test_default_enum_reuse() -> None:
    class Foo(Enum):
        BAR = "bar"
        BAZ = "baz"

    @strawberry.type
    class SomeType:
        foo: Foo
        bar: Foo

    definition = get_object_definition(SomeType, strict=True)
    assert definition.fields[1].type is definition.fields[1].type


def test_default_enum_with_enum_value() -> None:
    class Foo(Enum):
        BAR = "bar"
        BAZ = strawberry.enum_value("baz")

    @strawberry.type
    class Query:
        @strawberry.field
        def foo(self, foo: Foo) -> str:
            return foo.value

    schema = strawberry.Schema(Query)
    res = schema.execute_sync("{ foo(foo: BAZ) }")
    assert not res.errors
    assert res.data
    assert res.data["foo"] == "baz"
