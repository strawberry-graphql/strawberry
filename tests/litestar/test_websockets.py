import pytest

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL


def test_turning_off_graphql_ws():
    from litestar.exceptions import WebSocketDisconnect
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_graphql_transport_ws():
    from litestar.exceptions import WebSocketDisconnect
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    app = create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]):
            pass

    assert exc.value.code == 4406


def test_turning_off_all_ws_protocols():
    from litestar.exceptions import WebSocketDisconnect
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

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
    from litestar.exceptions import WebSocketDisconnect
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

    app = create_app(subscription_protocols=[])
    test_client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc:
        with test_client.websocket_connect("/graphql", ["imaginary-protocol"]):
            pass

    assert exc.value.code == 4406


def test_clients_can_prefer_protocols():
    from litestar.testing import TestClient
    from tests.litestar.app import create_app

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
