from __future__ import annotations

import sys
import typing
from collections import abc  # noqa: F401

import pytest

import strawberry


@pytest.mark.asyncio
async def test_subscription():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(self) -> typing.AsyncGenerator[str, None]:
            yield "Hi"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { example }"

    sub = await schema.subscribe(query)
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
        async def example(self, name: str) -> typing.AsyncGenerator[str, None]:
            yield f"Hi {name}"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = 'subscription { example(name: "Nina") }'

    sub = await schema.subscribe(query)
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi Nina"


requires_builtin_generics = pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="built-in generic annotations were added in python 3.9",
)


@pytest.mark.parametrize(
    "return_annotation",
    (
        "typing.AsyncGenerator[str, None]",
        "typing.AsyncIterable[str]",
        "typing.AsyncIterator[str]",
        pytest.param("abc.AsyncIterator[str]", marks=requires_builtin_generics),
        pytest.param("abc.AsyncGenerator[str, None]", marks=requires_builtin_generics),
        pytest.param("abc.AsyncIterable[str]", marks=requires_builtin_generics),
    ),
)
@pytest.mark.asyncio
async def test_subscription_return_annotations(return_annotation: str):
    async def async_resolver():
        yield "Hi"

    async_resolver.__annotations__["return"] = return_annotation

    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:

        example = strawberry.subscription(resolver=async_resolver)

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { example }"

    sub = await schema.subscribe(query)
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi"
