import typing
from enum import Enum

import pytest

import strawberry
from graphql import GraphQLEnumType, GraphQLEnumValue, graphql_sync
from strawberry.exceptions import NotAnEnum


def test_create_enum():
    @strawberry.enum
    class StringTest(Enum):
        A = "c"
        B = "i"
        C = "a"
        D = "o"

    assert StringTest.field

    assert type(StringTest.field) == GraphQLEnumType
    assert StringTest.field.name == "StringTest"

    assert StringTest.field.values == {
        "A": GraphQLEnumValue("c"),
        "B": GraphQLEnumValue("i"),
        "C": GraphQLEnumValue("a"),
        "D": GraphQLEnumValue("o"),
    }

    @strawberry.enum
    class IntTest(Enum):
        A = 1
        B = 2
        C = 3

    assert IntTest.field

    assert type(IntTest.field) == GraphQLEnumType
    assert IntTest.field.name == "IntTest"

    assert IntTest.field.values == {
        "A": GraphQLEnumValue(1),
        "B": GraphQLEnumValue(2),
        "C": GraphQLEnumValue(3),
    }

    @strawberry.enum
    class ComplexTest(Enum):
        MERCURY = (3.303e23, 2.4397e6)
        VENUS = (4.869e24, 6.0518e6)
        EARTH = (5.976e24, 6.37814e6)
        MARS = (6.421e23, 3.3972e6)
        JUPITER = (1.9e27, 7.1492e7)
        SATURN = (5.688e26, 6.0268e7)
        URANUS = (8.686e25, 2.5559e7)
        NEPTUNE = (1.024e26, 2.4746e7)

        def __init__(self, mass, radius):
            self.mass = mass
            self.radius = radius

        @property
        def surface_gravity(self):
            G = 6.67300e-11
            return G * self.mass / (self.radius * self.radius)

    assert ComplexTest.field

    assert type(ComplexTest.field) == GraphQLEnumType
    assert ComplexTest.field.name == "ComplexTest"

    assert ComplexTest.field.values == {
        "MERCURY": GraphQLEnumValue((3.303e23, 2.4397e6)),
        "VENUS": GraphQLEnumValue((4.869e24, 6.0518e6)),
        "EARTH": GraphQLEnumValue((5.976e24, 6.37814e6)),
        "MARS": GraphQLEnumValue((6.421e23, 3.3972e6)),
        "JUPITER": GraphQLEnumValue((1.9e27, 7.1492e7)),
        "SATURN": GraphQLEnumValue((5.688e26, 6.0268e7)),
        "URANUS": GraphQLEnumValue((8.686e25, 2.5559e7)),
        "NEPTUNE": GraphQLEnumValue((1.024e26, 2.4746e7)),
    }


def test_create_enum_with_custom_name():
    @strawberry.enum(name="NewName")
    class Test(Enum):
        A = 1
        B = 2
        C = 3

    assert Test.field

    assert type(Test.field) == GraphQLEnumType
    assert Test.field.name == "NewName"


def test_create_enum_with_arguments():
    @strawberry.enum(name="NewName", description="This is the description")
    class Test(Enum):
        A = 1
        B = 2
        C = 3

    assert Test.field

    assert type(Test.field) == GraphQLEnumType
    assert Test.field.name == "NewName"
    assert Test.field.description == "This is the description"

    @strawberry.enum(name="Example")
    class Test2(Enum):
        """Example"""

        A = 1
        B = 2
        C = 3

    assert Test.field

    assert type(Test2.field) == GraphQLEnumType
    assert Test2.field.name == "Example"
    assert Test2.field.description == "Example"


def test_raises_error_when_using_enum_with_a_not_enum_class():
    with pytest.raises(NotAnEnum) as e:

        @strawberry.enum
        class NormalClass:
            hello = "world"

    assert ("strawberry.enum can only be used with subclasses of Enum",) == e.value.args


def test_enum_resolver():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavour(self, info) -> IceCreamFlavour:
            return IceCreamFlavour.STRAWBERRY

    assert Query().best_flavour(None) == IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavour }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["bestFlavour"] == "STRAWBERRY"

    @strawberry.type
    class Cone:
        flavour: IceCreamFlavour

    @strawberry.type
    class Query:
        @strawberry.field
        def cone(self, info) -> Cone:
            return Cone(flavour=IceCreamFlavour.STRAWBERRY)

    assert Query().cone(None).flavour == IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query)

    query = "{ cone { flavour } }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["cone"]["flavour"] == "STRAWBERRY"


def test_enum_arguments():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def flavour_available(self, info, flavour: IceCreamFlavour) -> bool:
            return flavour == IceCreamFlavour.STRAWBERRY

    @strawberry.input
    class ConeInput:
        flavour: IceCreamFlavour

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def eat_cone(self, info, input: ConeInput) -> bool:
            return input.flavour == IceCreamFlavour.STRAWBERRY

    assert Query().flavour_available(None, IceCreamFlavour.VANILLA) is False
    assert Query().flavour_available(None, IceCreamFlavour.STRAWBERRY) is True

    input_bad = ConeInput(flavour=IceCreamFlavour.VANILLA)
    input_good = ConeInput(flavour=IceCreamFlavour.STRAWBERRY)

    assert Mutation().eat_cone(None, input_bad) is False
    assert Mutation().eat_cone(None, input_good) is True

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "{ flavourAvailable(flavour: VANILLA) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["flavourAvailable"] is False

    query = "{ flavourAvailable(flavour: STRAWBERRY) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["flavourAvailable"] is True

    query = "mutation { eatCone(input: { flavour: VANILLA }) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["eatCone"] is False

    query = "mutation { eatCone(input: { flavour: STRAWBERRY }) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["eatCone"] is True


def test_enum_falsy_values():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = ""
        STRAWBERRY = 0

    @strawberry.input
    class Input:
        flavour: IceCreamFlavour
        optionalFlavour: typing.Optional[IceCreamFlavour]

    @strawberry.type
    class Query:
        @strawberry.field
        def print_flavour(self, info, input: Input) -> str:
            return f"{input.flavour.value}"

    schema = strawberry.Schema(query=Query)

    query = "{ printFlavour(input: { flavour: VANILLA }) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["printFlavour"] == ""

    query = "{ printFlavour(input: { flavour: STRAWBERRY }) }"
    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["printFlavour"] == "0"
