import strawberry
from fastapi import FastAPI
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter
from strawberry.types import ExecutionResult, Info
from tests.fastapi.app import create_app


def test_can_set_background_task():
    task_complete = False

    def task():
        nonlocal task_complete
        task_complete = True

    @strawberry.type
    class Query:
        @strawberry.field
        def something(self, info: Info) -> str:
            tasks = info.context["background_tasks"]
            tasks.add_task(task)
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ something }"})

    assert response.json() == {"data": {"something": "foo"}}
    assert task_complete


def test_custom_context():
    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)
    app = create_app(schema=schema)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ customContextValue }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"customContextValue": "Hi!"}}


def test_custom_process_result():
    class CustomGraphQL(GraphQLRouter):
        async def process_result(self, request, result: ExecutionResult):
            return {}

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "ABC"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = CustomGraphQL(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {}
