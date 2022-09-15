from starlette.background import BackgroundTask
from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL as BaseGraphQL
from strawberry.types import ExecutionResult, Info


def test_simple_query(graphql_client):
    query = "{ hello }"

    response = graphql_client.query(query=query)

    assert response.data == {"hello": "Hello world"}


def test_fails_when_request_body_has_invalid_json(test_client):
    response = test_client.post(
        "/", data='{"qeury": "{__typena"', headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


def test_returns_errors(graphql_client):
    query = "{ donut }"

    response = graphql_client.query(query=query, asserts_errors=False)

    assert response.errors == [
        {
            "locations": [{"column": 3, "line": 1}],
            "message": "Cannot query field 'donut' on type 'Query'.",
        }
    ]


def test_can_pass_variables(graphql_client):
    query = "query Hello($name: String!) { hello(name: $name) }"

    response = graphql_client.query(query=query, variables={"name": "James"})

    assert response.data == {"hello": "Hello James"}


def test_returns_errors_and_data(graphql_client):
    query = "{ hello, alwaysFail }"

    response = graphql_client.query(query=query, asserts_errors=False)

    assert response.data == {"hello": "Hello world", "alwaysFail": None}
    assert response.errors == [
        {
            "locations": [{"column": 10, "line": 1}],
            "message": "You are not authorized",
            "path": ["alwaysFail"],
        }
    ]


def test_root_value(graphql_client):
    query = "{ rootName }"

    response = graphql_client.query(query=query)

    assert response.data == {"rootName": "Query"}


def test_context_response():
    @strawberry.type
    class Query:
        @strawberry.field
        def something(self, info: Info) -> str:
            r = info.context["response"]
            r.raw_headers.append((b"x-bar", b"bar"))
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = BaseGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ something }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"something": "foo"}}
    assert response.headers.get("x-bar") == "bar"


def test_can_set_custom_status_code():
    @strawberry.type
    class Query:
        @strawberry.field
        def something(self, info: Info) -> str:
            r = info.context["response"]
            r.status_code = 418
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = BaseGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ something }"})

    assert response.status_code == 418
    assert response.json() == {"data": {"something": "foo"}}


def test_can_set_background_task():
    task_complete = False

    def task():
        nonlocal task_complete
        task_complete = True

    @strawberry.type
    class Query:
        @strawberry.field
        def something(self, info: Info) -> str:
            r = info.context["response"]
            r.background = BackgroundTask(task)
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = BaseGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ something }"})

    assert response.json() == {"data": {"something": "foo"}}
    assert task_complete


def test_custom_context():
    class CustomGraphQL(BaseGraphQL):
        async def get_context(self, request, response):
            return {
                "request": request,
                "custom_context_value": "Hi!",
            }

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
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
        def abc(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)
    app = CustomGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {}
