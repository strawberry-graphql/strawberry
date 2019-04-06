import textwrap
import typing

import pytest

import strawberry
from graphql.language import parse
from graphql.subscription import subscribe


def test_subscription_type():
    @strawberry.type
    class MySub:
        @strawberry.subscription
        async def x(self, info) -> typing.AsyncGenerator[str, None]:
            yield "Hi"

    expected_representation = """
    type MySub {
      x: String!
    }
    """

    assert repr(MySub()) == textwrap.dedent(expected_representation).strip()


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
