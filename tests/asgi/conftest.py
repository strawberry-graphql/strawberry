import asyncio
import typing
from typing import Optional

import pytest

import strawberry
from starlette.testclient import TestClient
from strawberry.asgi import GraphQL
from strawberry.permission import BasePermission


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source, info):
        return False


@pytest.fixture
def schema():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info, name: typing.Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

        @strawberry.field(permission_classes=[AlwaysFailPermission])
        def always_fail(self, info) -> Optional[str]:
            return "Hey"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def example(self, info) -> typing.AsyncGenerator[str, None]:
            await asyncio.sleep(1.5)

            yield "Hi"

        @strawberry.subscription
        async def example_error(self, info) -> typing.AsyncGenerator[str, None]:
            raise ValueError("This is an example")

            yield "Hi"

    return strawberry.Schema(Query, subscription=Subscription)


@pytest.fixture
def test_client(schema):
    app = GraphQL(schema)

    return TestClient(app)


@pytest.fixture
def test_client_keep_alive(schema):
    app = GraphQL(schema, keep_alive=True, keep_alive_interval=2)

    return TestClient(app)
