import json

from django.test.client import RequestFactory

import strawberry
from strawberry.contrib.django.views import GraphQLView


@strawberry.type
class Query:
    hello: str = "strawberry"

    @strawberry.field
    async def hello_async(root, info) -> str:
        return "async strawberry"


schema = strawberry.Schema(query=Query)


def test_playground_view():
    factory = RequestFactory()

    request = factory.get("/graphql/", HTTP_ACCEPT="text/html")

    response = GraphQLView.as_view(schema=schema)(request)
    body = response.content.decode()

    assert "GraphQL Playground" in body
    assert f'endpoint: "{request.get_full_path()}"' in body


def test_graphql_query():

    query = "{ hello }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["hello"] == "strawberry"


def test_async_graphql_query():

    query = "{ hello_async }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["hello"] == "async strawberry"
