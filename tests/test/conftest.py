from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import pytest

from tests.views.schema import schema

if TYPE_CHECKING:
    from strawberry.test import BaseGraphQLTestClient


@asynccontextmanager
async def aiohttp_graphql_client() -> AsyncGenerator[BaseGraphQLTestClient]:
    try:
        from aiohttp import web
        from aiohttp.test_utils import TestClient, TestServer
        from strawberry.aiohttp.test import GraphQLTestClient
        from strawberry.aiohttp.views import GraphQLView
    except ImportError:
        pytest.skip("Aiohttp not installed")

    view = GraphQLView(schema=schema)
    app = web.Application()
    app.router.add_route("*", "/graphql/", view)

    async with TestClient(TestServer(app)) as client:
        yield GraphQLTestClient(client)


@asynccontextmanager
async def asgi_graphql_client() -> AsyncGenerator[BaseGraphQLTestClient]:
    try:
        from starlette.testclient import TestClient

        from strawberry.asgi import GraphQL
        from strawberry.asgi.test import GraphQLTestClient
    except ImportError:
        pytest.skip("Starlette not installed")

    yield GraphQLTestClient(TestClient(GraphQL(schema)))


@asynccontextmanager
async def django_graphql_client() -> AsyncGenerator[BaseGraphQLTestClient]:
    try:
        from django.test.client import Client

        from strawberry.django.test import GraphQLTestClient
    except ImportError:
        pytest.skip("Django not installed")

    yield GraphQLTestClient(Client())


@pytest.fixture(
    params=[
        pytest.param(aiohttp_graphql_client, marks=[pytest.mark.aiohttp]),
        pytest.param(asgi_graphql_client, marks=[pytest.mark.asgi]),
        pytest.param(django_graphql_client, marks=[pytest.mark.django]),
    ]
)
async def graphql_client(request) -> AsyncGenerator[BaseGraphQLTestClient]:
    async with request.param() as graphql_client:
        yield graphql_client
