from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

import pytest
from django.test.client import Client
from starlette.testclient import TestClient as AsgiTestClient

import aiohttp.web
from aiohttp.test_utils import TestClient as AiohttpTestClient
from aiohttp.test_utils import TestServer
from strawberry.aiohttp.test import GraphQLTestClient as AiohttpGraphQLTestClient
from strawberry.aiohttp.views import GraphQLView
from strawberry.asgi import GraphQL
from strawberry.asgi.test import GraphQLTestClient as AsgiGraphQLTestClient
from strawberry.django.test import GraphQLTestClient as DjangoGraphQLTestClient
from tests.views.schema import schema

if TYPE_CHECKING:
    from strawberry.test import BaseGraphQLTestClient


@asynccontextmanager
async def aiohttp_graphql_client() -> AsyncGenerator[AiohttpGraphQLTestClient]:
    view = GraphQLView(schema=schema)
    app = aiohttp.web.Application()
    app.router.add_route("*", "/graphql/", view)

    async with AiohttpTestClient(TestServer(app)) as client:
        yield AiohttpGraphQLTestClient(client)


@asynccontextmanager
async def asgi_graphql_client() -> AsyncGenerator[AsgiGraphQLTestClient]:
    yield AsgiGraphQLTestClient(AsgiTestClient(GraphQL(schema)))


@asynccontextmanager
async def django_graphql_client() -> AsyncGenerator[DjangoGraphQLTestClient]:
    yield DjangoGraphQLTestClient(Client())


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
