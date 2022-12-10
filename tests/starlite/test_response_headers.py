import strawberry
from starlite import Starlite
from starlite.testing import TestClient
from strawberry.starlite import make_graphql_controller
from strawberry.types import Info


# TODO: move this to common tests
def test_set_response_headers():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].headers["X-Strawberry"] = "rocks"
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert response.headers["x-strawberry"] == "rocks"


def test_set_cookie_headers():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].set_cookie(
                key="strawberry",
                value="rocks",
            )
            info.context["response"].set_cookie(
                key="Starlite",
                value="rocks",
            )
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert response.headers["set-cookie"] == (
        "Starlite=rocks; Path=/; SameSite=lax, "
        "strawberry=rocks; Path=/; SameSite=lax"
    )
