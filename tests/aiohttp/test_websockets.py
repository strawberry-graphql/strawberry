from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from aiohttp.test_utils import TestClient


async def test_turning_off_graphql_ws(
    aiohttp_client: Callable[..., Awaitable[TestClient]]
) -> None:
    from .app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.protocol is None
        assert ws.closed
        assert ws.close_code == 4406
        assert data.extra == "Subprotocol not acceptable"


async def test_turning_off_graphql_transport_ws(
    aiohttp_client: Callable[..., Awaitable[TestClient]]
):
    from .app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.protocol is None
        assert ws.closed
        assert ws.close_code == 4406
        assert data.extra == "Subprotocol not acceptable"


async def test_turning_off_all_ws_protocols(
    aiohttp_client: Callable[..., Awaitable[TestClient]]
):
    from .app import create_app

    app = create_app(subscription_protocols=[])
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.protocol is None
        assert ws.closed
        assert ws.close_code == 4406
        assert data.extra == "Subprotocol not acceptable"

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.protocol is None
        assert ws.closed
        assert ws.close_code == 4406
        assert data.extra == "Subprotocol not acceptable"


async def test_unsupported_ws_protocol(
    aiohttp_client: Callable[..., Awaitable[TestClient]]
):
    from .app import create_app

    app = create_app(subscription_protocols=[])
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=["imaginary-protocol"]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.protocol is None
        assert ws.closed
        assert ws.close_code == 4406
        assert data.extra == "Subprotocol not acceptable"


async def test_clients_can_prefer_protocols(
    aiohttp_client: Callable[..., Awaitable[TestClient]]
):
    from .app import create_app

    app = create_app(
        subscription_protocols=[GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    )
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
    ) as ws:
        assert ws.protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        assert ws.protocol == GRAPHQL_WS_PROTOCOL
