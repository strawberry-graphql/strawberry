from tests.fastapi.app import create_app

import strawberry
from starlite.testing import TestClient
from strawberry.types import Info


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
