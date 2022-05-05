from starlette.background import BackgroundTask
from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL as BaseGraphQL
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
            r = info.context["response"]
            r.background = BackgroundTask(task)
            return "foo"

    schema = strawberry.Schema(query=Query)
    app = BaseGraphQL(schema)

    test_client = TestClient(app)
    response = test_client.post("/", json={"query": "{ something }"})

    assert response.json() == {"data": {"something": "foo"}}
    assert task_complete
