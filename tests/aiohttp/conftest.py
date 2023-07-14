from __future__ import annotations

from asyncio import BaseEventLoop
from typing import TYPE_CHECKING, Awaitable, Callable

import pytest
import pytest_asyncio

from strawberry.aiohttp.test.client import GraphQLTestClient

if TYPE_CHECKING:
    from aiohttp.test_utils import TestClient


@pytest_asyncio.fixture
async def aiohttp_app_client(
    event_loop: BaseEventLoop, aiohttp_client: Callable[..., Awaitable[TestClient]]
) -> TestClient:
    from tests.aiohttp.app import create_app

    app = create_app(graphiql=True)
    event_loop.set_debug(True)
    return await aiohttp_client(app)


@pytest_asyncio.fixture
async def aiohttp_app_client_no_get(
    event_loop: BaseEventLoop, aiohttp_client: Callable[..., Awaitable[TestClient]]
) -> TestClient:
    from tests.aiohttp.app import create_app

    app = create_app(graphiql=True, allow_queries_via_get=False)
    event_loop.set_debug(True)
    return await aiohttp_client(app)


@pytest.fixture
def graphql_client(aiohttp_app_client: TestClient) -> GraphQLTestClient:
    return GraphQLTestClient(aiohttp_app_client, url="/graphql")
