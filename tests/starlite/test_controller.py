from typing import AsyncGenerator, Optional

import pytest

import strawberry
from starlite import Starlite
from starlite.exceptions import ImproperlyConfiguredException
from starlite.testing import TestClient
from strawberry.starlite import make_graphql_controller
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)


def test_websocket_path():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def echo(self) -> AsyncGenerator[str, None]:
            yield "Hi!"

    schema = strawberry.Schema(query=Query, subscription=Subscription)
    GraphQLController = make_graphql_controller(
        schema=schema, path="/graphql", websocket_path="/customWs"
    )
    app = Starlite(route_handlers=[GraphQLController])
    test_client = TestClient(app)

    with test_client.websocket_connect(
        "/graphql/customWs", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="subscription { echo }"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(id="sub1", payload={"data": {"echo": "Hi!"}}).as_dict()
        )


def test_empty_websocket_path():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def echo(self) -> AsyncGenerator[str, None]:
            yield "Hi!"

    schema = strawberry.Schema(query=Query, subscription=Subscription)
    with pytest.raises(
        ImproperlyConfiguredException, match="webocket_path must not be empty"
    ):
        make_graphql_controller(schema=schema, path="/graphql", websocket_path="")
