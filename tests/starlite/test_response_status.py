from starlette import status

import strawberry
from starlite import Starlite
from starlite.testing import TestClient
from strawberry.starlite import make_graphql_controller
from strawberry.types import Info


# TODO: move this to common tests
def test_set_custom_http_response_status():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].status_code = status.HTTP_418_IM_A_TEAPOT
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 418
    assert response.json() == {"data": {"abc": "abc"}}


def test_set_without_setting_http_response_status():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
