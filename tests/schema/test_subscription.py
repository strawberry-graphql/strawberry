# ruff: noqa: F821
from __future__ import annotations

import sys
from collections import abc  # noqa: F401
from typing import AsyncGenerator, AsyncIterable, AsyncIterator, Union  # noqa: F401
from typing_extensions import Annotated

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
        async def example(self) -> AsyncGenerator[str, None]:
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
        async def example(self, name: str) -> AsyncGenerator[str, None]:
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
        "AsyncGenerator[str, None]",
        "AsyncIterable[str]",
        "AsyncIterator[str]",
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


@pytest.mark.asyncio
async def test_subscription_with_unions():
    global A, B

    @strawberry.type
    class A:
        a: str

    @strawberry.type
    class B:
        b: str

    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example_with_union(self) -> AsyncGenerator[Union[A, B], None]:
            yield A(a="Hi")

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { exampleWithUnion { ... on A { a } } }"

    sub = await schema.subscribe(query)
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["exampleWithUnion"]["a"] == "Hi"

    del A, B


@pytest.mark.asyncio
async def test_subscription_with_unions_and_annotated():
    global C, D

    @strawberry.type
    class C:
        c: str

    @strawberry.type
    class D:
        d: str

    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example_with_annotated_union(
            self,
        ) -> AsyncGenerator[
            Annotated[Union[C, D], strawberry.union("UnionName")], None
        ]:
            yield C(c="Hi")

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { exampleWithAnnotatedUnion { ... on C { c } } }"

    sub = await schema.subscribe(query)
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["exampleWithAnnotatedUnion"]["c"] == "Hi"

    del C, D


@pytest.mark.asyncio
async def test_subscription_with_annotated():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(
            self,
        ) -> Annotated[AsyncGenerator[str, None], "this doesn't matter"]:
            yield "Hi"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { example }"

    sub = await schema.subscribe(query)
    result = await sub.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi"
