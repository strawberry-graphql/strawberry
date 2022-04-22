from typing import Dict

import pytest

from starlette.testclient import TestClient

import strawberry
from fastapi import Depends, FastAPI
from strawberry.exceptions import InvalidCustomContext
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.types import Info


def test_base_context():
    base_context = BaseContext()
    assert base_context.request is None
    assert base_context.background_tasks is None
    assert base_context.response is None


def test_with_class_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.request is not None
            assert info.context.strawberry == "rocks"
            return "abc"

    class CustomContext(BaseContext):
        def __init__(self, rocks: str):
            self.strawberry = rocks

    def custom_context_dependency() -> CustomContext:
        return CustomContext(rocks="rocks")

    def get_context(custom_context: CustomContext = Depends(custom_context_dependency)):
        return custom_context

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_dict_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") == "rocks"
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    def get_context(value: str = Depends(custom_context_dependency)) -> Dict[str, str]:
        return {"strawberry": value}

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_without_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema, context_getter=None)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_with_invalid_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("request") is not None
            assert info.context.get("strawberry") is None
            return "abc"

    def custom_context_dependency() -> str:
        return "rocks"

    def get_context(value: str = Depends(custom_context_dependency)) -> str:
        return value

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema=schema, context_getter=get_context)
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


def test_transport_specific_context_getter():
    @strawberry.type
    class Query:
        @strawberry.field
        def transport(self, info: Info) -> str:
            return info.context.get("transport", "")

    def http_get_context_getter() -> Dict[str, str]:
        return {"transport": "get"}

    def http_post_context_getter() -> Dict[str, str]:
        return {"transport": "post"}

    def ws_context_getter() -> Dict[str, str]:
        return {"transport": "ws"}

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(
        schema=schema,
        http_get_context_getter=http_get_context_getter,
        http_post_context_getter=http_post_context_getter,
        ws_context_getter=ws_context_getter,
    )
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)

    response = test_client.post("/graphql", json={"query": "{ transport }"})
    assert response.status_code == 200
    assert response.json() == {"data": {"transport": "post"}}

    response = test_client.get("/graphql", params={"query": "{ transport }"})
    assert response.status_code == 200
    assert response.json() == {"data": {"transport": "get"}}

    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="query { transport }"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(id="sub1", payload={"data": {"transport": "ws"}}).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()
