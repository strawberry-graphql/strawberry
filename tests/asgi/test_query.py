from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.types import ExecutionResult


def test_simple_query(schema, test_client):
    response = test_client.post("/", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}


def test_returns_errors(schema, test_client):
    response = test_client.post("/", json={"query": "{ donut }"})

    assert response.json() == {
        "data": None,
        "errors": [
            {
                "locations": [{"column": 3, "line": 1}],
                "message": "Cannot query field 'donut' on type 'Query'.",
                "path": None,
            }
        ],
    }


def test_can_pass_variables(schema, test_client):
    response = test_client.post(
        "/",
        json={
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": {"name": "James"},
        },
    )

    assert response.json() == {"data": {"hello": "Hello James"}}


def test_returns_errors_and_data(schema, test_client):
    response = test_client.post("/", json={"query": "{ hello, alwaysFail }"})

    assert response.status_code == 200
    assert response.json() == {
        "data": {"hello": "Hello world", "alwaysFail": None},
        "errors": [
            {
                "locations": [{"column": 10, "line": 1}],
                "message": "You are not authorized",
                "path": ["alwaysFail"],
            }
        ],
    }


def test_root_value(schema, test_client):
    response = test_client.post("/", json={"query": "{ rootName }"})

    assert response.json() == {"data": {"rootName": "Query"}}


def test_custom_context():
    class CustomGraphQL(BaseGraphQL):
        async def get_context(self, request):
            return {
                "request": request,
                "custom_context_value": "Hi!",
            }

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info) -> str:
            return info.context["custom_context_value"]

    schema = strawberry.Schema(query=Query)
    app = CustomGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ customContextValue }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"customContextValue": "Hi!"}}


def test_custom_process_result():
    class CustomGraphQL(BaseGraphQL):
        async def process_result(self, request, result: ExecutionResult):
            return {}

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)
    app = CustomGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {}
