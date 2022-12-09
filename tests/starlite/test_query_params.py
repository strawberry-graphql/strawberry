import strawberry
from starlite import Starlite, status_codes
from starlite.testing import TestClient
from strawberry.starlite import make_graphql_controller


def test_no_graphiql_no_query():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    schema = strawberry.Schema(query=Query)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, graphiql=False
    )
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"variables": '{"name": "James"}'})

    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


def test_get_with_query_params(test_client):
    response = test_client.get("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"data": {"hello": "Hello world"}}


def test_can_pass_variables_with_query_params(test_client):
    response = test_client.get(
        "/graphql",
        params={
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": '{"name": "James"}',
        },
    )

    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"data": {"hello": "Hello James"}}


def test_post_fails_with_query_params(test_client):
    response = test_client.post("/graphql", params={"query": "{ abc }"})

    assert response.status_code == status_codes.HTTP_415_UNSUPPORTED_MEDIA_TYPE


def test_does_not_allow_mutation(test_client):
    response = test_client.get("/graphql", params={"query": "mutation { abc }"})

    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.text == "mutations are not allowed when using GET"


def test_fails_if_allow_queries_via_get_false(test_client):
    @strawberry.type
    class Query:
        abc: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def abc(self) -> str:
            return "abc"

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    graphql_controller = make_graphql_controller(
        path="/graphql", schema=schema, allow_queries_via_get=False
    )
    app = Starlite(route_handlers=[graphql_controller])

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"query": "{ abc }"})

    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.text == "queries are not allowed when using GET"
