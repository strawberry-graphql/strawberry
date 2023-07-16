from typing import Any

import pytest

import strawberry
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL


def test_turning_off_graphql_ws():
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    from tests.fastapi.app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_graphql_transport_ws():
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    from tests.fastapi.app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_all_ws_protocols():
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    from tests.fastapi.app import create_app

    app = create_app(subscription_protocols=[])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_unsupported_ws_protocol():
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    from tests.fastapi.app import create_app

    app = create_app(subscription_protocols=[])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", ["imaginary-protocol"]):
            pass

    assert exc.value.code == 4406


def test_clients_can_prefer_protocols():
    from starlette.testclient import TestClient

    from tests.fastapi.app import create_app

    app = create_app(
        subscription_protocols=[GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    )
    test_client = TestClient(app)

    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
    ) as ws:
        assert ws.accepted_subprotocol == GRAPHQL_TRANSPORT_WS_PROTOCOL

    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        assert ws.accepted_subprotocol == GRAPHQL_WS_PROTOCOL


def test_with_custom_encode_json():
    from starlette.testclient import TestClient

    from fastapi import FastAPI
    from strawberry.fastapi.router import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    class MyRouter(GraphQLRouter[None, None]):
        def encode_json(self, response_data: Any):
            return '"custom"'

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = MyRouter(schema=schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == "custom"
