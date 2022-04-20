import typing
from enum import Enum
from textwrap import dedent
from typing import List, Optional

import pytest

import strawberry


def test_enum_resolver():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavour(self) -> IceCreamFlavour:
            return IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavour }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["bestFlavour"] == "STRAWBERRY"

    @strawberry.type
    class Cone:
        flavour: IceCreamFlavour

    @strawberry.type
    class Query:
        @strawberry.field
        def cone(self) -> Cone:
            return Cone(flavour=IceCreamFlavour.STRAWBERRY)

    schema = strawberry.Schema(query=Query)

    query = "{ cone { flavour } }"

    result = schema.execute_sync(query)

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
        def flavour_available(self, flavour: IceCreamFlavour) -> bool:
            return flavour == IceCreamFlavour.STRAWBERRY

    @strawberry.input
    class ConeInput:
        flavour: IceCreamFlavour

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def eat_cone(self, input: ConeInput) -> bool:
            return input.flavour == IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "{ flavourAvailable(flavour: VANILLA) }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["flavourAvailable"] is False

    query = "{ flavourAvailable(flavour: STRAWBERRY) }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["flavourAvailable"] is True

    query = "mutation { eatCone(input: { flavour: VANILLA }) }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["eatCone"] is False

    query = "mutation { eatCone(input: { flavour: STRAWBERRY }) }"
    result = schema.execute_sync(query)

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
        optionalFlavour: typing.Optional[IceCreamFlavour] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def print_flavour(self, input: Input) -> str:
            return f"{input.flavour.value}"

    schema = strawberry.Schema(query=Query)

    query = "{ printFlavour(input: { flavour: VANILLA }) }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["printFlavour"] == ""

    query = "{ printFlavour(input: { flavour: STRAWBERRY }) }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["printFlavour"] == "0"


def test_enum_in_list():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
        PISTACHIO = "pistachio"

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavours(self) -> List[IceCreamFlavour]:
            return [IceCreamFlavour.STRAWBERRY, IceCreamFlavour.PISTACHIO]

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavours }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["bestFlavours"] == ["STRAWBERRY", "PISTACHIO"]


def test_enum_in_optional_list():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
        PISTACHIO = "pistachio"

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavours(self) -> Optional[List[IceCreamFlavour]]:
            return None

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavours }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["bestFlavours"] is None


@pytest.mark.asyncio
async def test_enum_resolver_async():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        async def best_flavour(self) -> IceCreamFlavour:
            return IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavour }"

    result = await schema.execute(query)

    assert not result.errors
    assert result.data["bestFlavour"] == "STRAWBERRY"


@pytest.mark.asyncio
async def test_enum_in_list_async():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
        PISTACHIO = "pistachio"

    @strawberry.type
    class Query:
        @strawberry.field
        async def best_flavours(self) -> List[IceCreamFlavour]:
            return [IceCreamFlavour.STRAWBERRY, IceCreamFlavour.PISTACHIO]

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavours }"

    result = await schema.execute(query)

    assert not result.errors
    assert result.data["bestFlavours"] == ["STRAWBERRY", "PISTACHIO"]


def test_enum_as_argument():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
        PISTACHIO = "pistachio"

    @strawberry.type
    class Query:
        @strawberry.field
        def create_flavour(self, flavour: IceCreamFlavour) -> str:
            return f"{flavour.name}"

    schema = strawberry.Schema(query=Query)

    expected = dedent(
        """
        enum IceCreamFlavour {
          VANILLA
          STRAWBERRY
          CHOCOLATE
          PISTACHIO
        }

        type Query {
          createFlavour(flavour: IceCreamFlavour!): String!
        }
        """
    ).strip()

    assert str(schema) == expected

    query = "{ createFlavour(flavour: CHOCOLATE) }"
    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["createFlavour"] == "CHOCOLATE"

    # Explicitly using `variable_values` now so that the enum is parsed using
    # `CustomGraphQLEnumType.parse_value()` instead of `.parse_literal`
    query = "query ($flavour: IceCreamFlavour!) { createFlavour(flavour: $flavour) }"
    result = schema.execute_sync(query, variable_values={"flavour": "VANILLA"})
    assert not result.errors
    assert result.data["createFlavour"] == "VANILLA"


def test_enum_as_default_argument():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
        PISTACHIO = "pistachio"

    @strawberry.type
    class Query:
        @strawberry.field
        def create_flavour(
            self, flavour: IceCreamFlavour = IceCreamFlavour.STRAWBERRY
        ) -> str:
            return f"{flavour.name}"

    schema = strawberry.Schema(query=Query)

    expected = dedent(
        """
        enum IceCreamFlavour {
          VANILLA
          STRAWBERRY
          CHOCOLATE
          PISTACHIO
        }

        type Query {
          createFlavour(flavour: IceCreamFlavour! = STRAWBERRY): String!
        }
        """
    ).strip()

    assert str(schema) == expected

    query = "{ createFlavour }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["createFlavour"] == "STRAWBERRY"


def test_enum_resolver_plain_value():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavour(self) -> IceCreamFlavour:
            return "strawberry"  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavour }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["bestFlavour"] == "STRAWBERRY"


def test_enum_deprecated_value():
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = strawberry.enum_value(
            "strawberry", deprecation_reason="We ran out"
        )
        CHOCOLATE = strawberry.enum_value("chocolate")

    @strawberry.type
    class Query:
        @strawberry.field
        def best_flavour(self) -> IceCreamFlavour:
            return IceCreamFlavour.STRAWBERRY

    schema = strawberry.Schema(query=Query)

    query = """
    {
        __type(name: "IceCreamFlavour") {
            enumValues(includeDeprecated: true) {
                name
                isDeprecated
                deprecationReason
            }
        }
    }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["__type"]["enumValues"] == [
        {"deprecationReason": None, "isDeprecated": False, "name": "VANILLA"},
        {"deprecationReason": "We ran out", "isDeprecated": True, "name": "STRAWBERRY"},
        {"deprecationReason": None, "isDeprecated": False, "name": "CHOCOLATE"},
    ]
