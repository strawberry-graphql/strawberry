import strawberry


# TODO: move this to common tests
def test_set_response_headers():
    from litestar import Litestar
    from litestar.testing import TestClient
    from strawberry.litestar import make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].headers["X-Strawberry"] = "rocks"
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Litestar(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert response.headers["x-strawberry"] == "rocks"


def test_set_cookie_headers():
    from litestar import Litestar
    from litestar.testing import TestClient
    from strawberry.litestar import make_graphql_controller

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: strawberry.Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].set_cookie(
                key="strawberry",
                value="rocks",
            )
            info.context["response"].set_cookie(
                key="Litestar",
                value="rocks",
            )
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(path="/graphql", schema=schema)
    app = Litestar(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert response.headers["set-cookie"] == (
        "strawberry=rocks; Path=/; SameSite=lax, Litestar=rocks; Path=/; SameSite=lax"
    )
