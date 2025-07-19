import strawberry
from strawberry.schema.config import StrawberryConfig
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, MyExtension, Query, Subscription


async def test_batch_graphql_query(http_client_class: type[HttpClient]):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 10}),
        )
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
    ]


async def test_returns_error_when_batching_is_disabled(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config=None),
        )
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "Batching is not enabled" in response.text


async def test_returns_error_when_trying_too_many_operations(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 2}),
        )
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "Too many operations" in response.text
