import asyncio
import typing
from typing import Optional

import pytest

from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.permission import BasePermission
from strawberry.types import Info


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        return False


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: typing.Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self) -> Optional[str]:
        return "Hey"

    @strawberry.field
    def root_name(root) -> str:
        return type(root).__name__


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def example(self) -> typing.AsyncGenerator[str, None]:
        await asyncio.sleep(1.5)

        yield "Hi"

    @strawberry.subscription
    async def example_error(self) -> typing.AsyncGenerator[str, None]:
        raise ValueError("This is an example")

        yield "Hi"

    @strawberry.subscription
    async def echo(
        self, message: str, delay: float = 0
    ) -> typing.AsyncGenerator[str, None]:
        await asyncio.sleep(delay)
        yield message


class GraphQL(BaseGraphQL):
    async def get_root_value(self, request):
        return Query()


@pytest.fixture
def schema():
    return strawberry.Schema(Query, subscription=Subscription)


@pytest.fixture
def test_client(schema):
    app = GraphQL(schema)

    return TestClient(app)


@pytest.fixture
def test_client_keep_alive(schema):
    app = GraphQL(schema, keep_alive=True, keep_alive_interval=2)

    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql(schema):
    app = GraphQL(schema, graphiql=False)

    return TestClient(app)
