import textwrap
import typing

import pytest

import strawberry
from graphql.language import parse
from graphql.subscription import subscribe
from strawberry.printer import print_type


def test_subscription_type():
    @strawberry.type
    class MySub:
        @strawberry.subscription
        async def x(self, info) -> typing.AsyncGenerator[str, None]:
            yield "Hi"

    expected_type = """
    type MySub {
      x: String!
    }
    """

    assert print_type(MySub()) == textwrap.dedent(expected_type).strip()


@pytest.mark.asyncio
async def test_subscription():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(self, info) -> typing.AsyncGenerator[str, None]:
            yield "Hi"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { example }"

    sub = await subscribe(schema, parse(query))
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi"


@pytest.mark.asyncio
async def test_subscription_with_arguments():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(self, info, name: str) -> typing.AsyncGenerator[str, None]:
            yield f"Hi {name}"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = 'subscription { example(name: "Nina") }'

    sub = await subscribe(schema, parse(query))
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi Nina"
