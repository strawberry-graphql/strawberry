# ruff: noqa: F821
from __future__ import annotations

from collections import abc  # noqa: F401
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator  # noqa: F401
from typing import (
    Annotated,
    Any,
    Union,
)

import pytest

import strawberry
from strawberry.types.execution import PreExecutionError
from strawberry.utils.aio import aclosing


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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi"


@pytest.mark.asyncio
async def test_subscription_with_permission():
    from strawberry import BasePermission

    class IsAuthenticated(BasePermission):
        message = "Unauthorized"

        async def has_permission(
            self, source: Any, info: strawberry.Info, **kwargs: Any
        ) -> bool:
            return True

    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription(permission_classes=[IsAuthenticated])
        async def example(self) -> AsyncGenerator[str, None]:
            yield "Hi"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = "subscription { example }"

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi Nina"


@pytest.mark.parametrize(
    "return_annotation",
    [
        "AsyncGenerator[str, None]",
        "AsyncIterable[str]",
        "AsyncIterator[str]",
        "abc.AsyncIterator[str]",
        "abc.AsyncGenerator[str, None]",
        "abc.AsyncIterable[str]",
    ],
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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

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

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

    assert not result.errors
    assert result.data["example"] == "Hi"


async def test_subscription_immediate_error():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription()
        async def example(self) -> AsyncGenerator[str, None]:
            return "fds"

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = """#graphql
        subscription { example }
    """

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

    assert isinstance(result, PreExecutionError)
    assert result.errors


async def test_wrong_operation_variables():
    @strawberry.type
    class Query:
        x: str = "Hello"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(self, name: str) -> AsyncGenerator[str, None]:
            yield f"Hi {name}"  # pragma: no cover

    schema = strawberry.Schema(query=Query, subscription=Subscription)

    query = """#graphql
        subscription subOp($opVar: String!){ example(name: $opVar) }
    """

    async with aclosing(await schema.subscribe(query)) as sub_result:
        result = await sub_result.__anext__()

    assert result.errors
    assert (
        result.errors[0].message
        == "Variable '$opVar' of required type 'String!' was not provided."
    )
