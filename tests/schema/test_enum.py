import typing
from enum import Enum
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
        def best_flavour(self, info) -> IceCreamFlavour:
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
        def cone(self, info) -> Cone:
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
        def print_flavour(self, info, input: Input) -> str:
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
        def best_flavours(self, info) -> List[IceCreamFlavour]:
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
        def best_flavours(self, info) -> Optional[List[IceCreamFlavour]]:
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
        async def best_flavour(self, info) -> IceCreamFlavour:
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
        async def best_flavours(self, info) -> List[IceCreamFlavour]:
            return [IceCreamFlavour.STRAWBERRY, IceCreamFlavour.PISTACHIO]

    schema = strawberry.Schema(query=Query)

    query = "{ bestFlavours }"

    result = await schema.execute(query)

    assert not result.errors
    assert result.data["bestFlavours"] == ["STRAWBERRY", "PISTACHIO"]
