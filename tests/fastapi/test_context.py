import asyncio
from typing import Any, AsyncGenerator, Dict

import pytest

import strawberry
from strawberry.exceptions import InvalidCustomContext
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_START,
    GQL_STOP,
)
from strawberry.types import Info


def test_base_context():
    from strawberry.fastapi import BaseContext

    base_context = BaseContext()
    assert base_context.request is None
    assert base_context.background_tasks is None
    assert base_context.response is None


def test_with_explicit_class_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import BaseContext, GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info[Any, None]) -> str:
            assert info.context.request is not None
            assert info.context.strawberry == "explicitly rocks"
            assert info.context.connection_params is None
            return "abc"

    class CustomContext(BaseContext):
        def __init__(self, rocks: str):
            self.strawberry = rocks

    def custom_context_dependency() -> CustomContext:
        return CustomContext(rocks="explicitly rocks")

    def get_context(custom_context: CustomContext = Depends(custom_context_dependency)):
        return custom_context

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_implicit_class_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import BaseContext, GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info[Any, None]) -> str:
            assert info.context.request is not None
            assert info.context.strawberry == "implicitly rocks"
            assert info.context.connection_params is None
            return "abc"

    class CustomContext(BaseContext):
        def __init__(self, rocks: str = "implicitly rocks"):
            super().__init__()
            self.strawberry = rocks

    def get_context(custom_context: CustomContext = Depends()):
        return custom_context

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_dict_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info[Any, None]) -> str:
            assert info.context.get("request") is not None
            assert "connection_params" not in info.context
            assert info.context.get("strawberry") == "rocks"
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    def get_context(value: str = Depends(custom_context_dependency)) -> Dict[str, str]:
        return {"strawberry": value}

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_without_context_getter():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info[Any, None]) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema, context_getter=None)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_invalid_context_getter():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info[Any, None]) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    def get_context(value: str = Depends(custom_context_dependency)) -> str:
        return value

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    with pytest.raises(
        InvalidCustomContext,
        match=(
            "The custom context must be either a class "
            "that inherits from BaseContext or a dictionary"
        ),
    ):
        test_client.post("/graphql", json={"query": "{ abc }"})


def test_class_context_injects_connection_params_over_transport_ws():
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import BaseContext, GraphQLRouter

    @strawberry.type
    class Query:
        x: str = "hi"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def connection_params(
            self, info: Info[Any, None], delay: float = 0
        ) -> AsyncGenerator[str, None]:
            assert info.context.request is not None
            await asyncio.sleep(delay)
            yield info.context.connection_params["strawberry"]

    class Context(BaseContext):
        strawberry: str

        def __init__(self):
            self.strawberry = "rocks"

    def get_context(context: Context = Depends()) -> Context:
        return context

    app = FastAPI()
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")
    test_client = TestClient(app)

    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage(payload={"strawberry": "rocks"}).as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="subscription { connectionParams }"
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"connectionParams": "rocks"}}
            ).as_dict()
        )

        ws.send_json(CompleteMessage(id="sub1").as_dict())

        ws.close()


def test_class_context_injects_connection_params_over_ws():
    from starlette.websockets import WebSocketDisconnect

    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from strawberry.fastapi import BaseContext, GraphQLRouter

    @strawberry.type
    class Query:
        x: str = "hi"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def connection_params(
            self, info: Info[Any, None], delay: float = 0
        ) -> AsyncGenerator[str, None]:
            assert info.context.request is not None
            await asyncio.sleep(delay)
            yield info.context.connection_params["strawberry"]

    class Context(BaseContext):
        strawberry: str

        def __init__(self):
            self.strawberry = "rocks"

    def get_context(context: Context = Depends()) -> Context:
        return context

    app = FastAPI()
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    graphql_app = GraphQLRouter[Any, None](schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")
    test_client = TestClient(app)

    with test_client.websocket_connect("/graphql", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json(
            {
                "type": GQL_CONNECTION_INIT,
                "id": "demo",
                "payload": {"strawberry": "rocks"},
            }
        )
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": "subscription { connectionParams }",
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"connectionParams": "rocks"}

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
