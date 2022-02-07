from typing import Dict

import pytest

from starlette.testclient import TestClient

import strawberry
from fastapi import Depends, FastAPI
from strawberry.exceptions import InvalidCustomContext
from strawberry.fastapi import BaseContext, GraphQLRouter
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
