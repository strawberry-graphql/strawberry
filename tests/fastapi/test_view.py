import pytest

from starlette import status
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from tests.fastapi.app import create_app


def test_renders_graphiql(test_client):
    response = test_client.get("/graphql")

    assert response.status_code == status.HTTP_200_OK

    assert "<title>Strawberry GraphiQL</title>" in response.text


def test_renders_graphiql_disabled(test_client_no_graphiql):
    response = test_client_no_graphiql.get("/graphql")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_turning_off_graphql_ws():
    app = create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_graphql_transport_ws():
    app = create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_all_ws_protocols():
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
    app = create_app(subscription_protocols=[])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", ["imaginary-protocol"]):
            pass

    assert exc.value.code == 4406


def test_clients_can_prefer_protocols():
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
