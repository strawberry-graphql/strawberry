import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from strawberry import Schema
from strawberry.fastapi import GraphQLRouter

from tests.asgi.conftest import schema


def construct_app(*args, **kwargs):
    app = FastAPI()

    router = GraphQLRouter(*args, **kwargs)

    app.include_router(
        router,
        prefix="/graphql",
        tags=["GraphQL"],
    )
    return app
 

@pytest.fixture
def test_client(schema):
    app = construct_app(schema)
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive(schema):
    app = construct_app(schema, keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql(schema):
    app = construct_app(schema, graphiql=False)
    return TestClient(app)
