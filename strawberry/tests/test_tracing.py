import asyncio

import strawberry
from starlette.testclient import TestClient
from strawberry.contrib.starlette.tests.helpers import create_query, get_graphql_app


def test_starlette_tracing():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    app = get_graphql_app(schema, tracing=True)
    client = TestClient(app)

    query = create_query(
        """
            query {
                hello
            }
        """
    )

    response = client.post("/graphql", json=query)
    print(response.content)
    assert response.status_code == 200

    json = response.json()
    assert type(json["extensions"]["tracing"]) == dict


def test_starlette_tracing_async():
    @strawberry.type
    class Query:
        @strawberry.field
        async def hello(self, info) -> str:
            await asyncio.sleep(1)
            return "world"

    schema = strawberry.Schema(query=Query)

    app = get_graphql_app(schema, tracing=True)
    client = TestClient(app)

    query = create_query(
        """
            query {
                hello
            }
        """
    )

    response = client.post("/graphql", json=query)
    print(response.content)
    assert response.status_code == 200

    json = response.json()
    assert type(json["extensions"]["tracing"]) == dict

    tracing_results = json["extensions"]["tracing"]
    assert tracing_results["duration"] >= 1000000000
    assert tracing_results["duration"] <= 1500000000


def test_starlette_tracing_disabled_without_flag():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    app = get_graphql_app(schema)
    client = TestClient(app)

    query = create_query(
        """
            query {
                hello
            }
        """
    )

    response = client.post("/graphql", json=query)
    assert response.status_code == 200

    json = response.json()
    assert "extensions" not in json
