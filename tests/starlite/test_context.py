from typing import Dict

import strawberry
from starlite import Provide, Starlite
from starlite.testing import TestClient
from strawberry.starlite import BaseContext, make_graphql_controller
from strawberry.types import Info


def test_base_context():
    base_context = BaseContext()
    assert base_context.request is None


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

    def get_context(custom_context_dependency: CustomContext):
        return custom_context_dependency

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Starlite(
        route_handlers=[graphql_controller],
        dependencies={"custom_context_dependency": Provide(custom_context_dependency)},
    )

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

    def get_context(custom_context_dependency: str) -> Dict[str, str]:
        return {"strawberry": custom_context_dependency}

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Starlite(
        route_handlers=[graphql_controller],
        dependencies={"custom_context_dependency": Provide(custom_context_dependency)},
    )
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

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=None
    )
    app = Starlite(route_handlers=[graphql_controller])
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

    def get_context(custom_context_dependency: str) -> str:
        return custom_context_dependency

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, context_getter=get_context
    )
    app = Starlite(
        route_handlers=[graphql_controller],
        dependencies={"custom_context_dependency": Provide(custom_context_dependency)},
    )
    test_client = TestClient(app, raise_server_exceptions=True)
    # FIXME:
    #! assert starlite.exceptions.http_exceptions.InternalServerException is raised
    # with pytest.raises(
    #     InternalServerException,
    #     r"A dependency failed validation for POST .*"
    # ),
    # ):
    response = test_client.post("/graphql", json={"query": "{ abc }"})
    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == "A dependency failed validation for POST http://testserver.local/graphql"
    )
