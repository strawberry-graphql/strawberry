from starlette import status
from starlette.testclient import TestClient

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


def test_no_graphiql_no_query():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema, graphiql=False)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"variables": "{ abc }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_no_graphiql_get_with_query_params():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema, graphiql=False)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"query": "{ abc }"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {"abc": "abc"}}


def test_post_fails_with_query_params():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", params={"query": "{ abc }"})

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


def test_does_not_allow_mutation():
    @strawberry.type
    class Query:
        abc: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"query": "mutation { abc }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.text == "mutations are not allowed when using GET"


def test_fails_if_allow_queries_via_get_false():
    @strawberry.type
    class Query:
        abc: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    graphql_app = GraphQLRouter(schema, allow_queries_via_get=False)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.get("/graphql", params={"query": "{ abc }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.text == "queries are not allowed when using GET"
