from typing import Type

from strawberry.schema.config import BatchingConfig, StrawberryConfig

from .clients import HttpClient


async def test_batch_graphql_query(http_client_class: Type[HttpClient]):
    http_client = http_client_class(
        schema_config=StrawberryConfig(batching_config=BatchingConfig())
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
    http_client_class: Type[HttpClient],
):
    http_client = http_client_class(
        schema_config=StrawberryConfig(batching_config=None)
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
    http_client_class: Type[HttpClient],
):
    http_client = http_client_class(
        schema_config=StrawberryConfig(batching_config=BatchingConfig(max_operations=2))
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
