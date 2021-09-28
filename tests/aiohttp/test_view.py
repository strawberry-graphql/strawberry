from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .app import create_app


async def test_graphiql_view(aiohttp_app_client):
    response = await aiohttp_app_client.get("/graphql", headers={"Accept": "text/html"})
    body = await response.text()

    assert "GraphiQL" in body


async def test_graphiql_disabled_view(aiohttp_client):
    app = create_app(graphiql=False)
    client = await aiohttp_client(app)

    response = await client.get("/graphql", headers={"Accept": "text/html"})
    assert response.status == 404


async def test_turning_off_graphql_ws(aiohttp_client):
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


async def test_turning_off_graphql_transport_ws(aiohttp_client):
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


async def test_turning_off_all_ws_protocols(aiohttp_client):
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


async def test_unsupported_ws_protocol(aiohttp_client):
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


async def test_clients_can_prefer_protocols(aiohttp_client):
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
