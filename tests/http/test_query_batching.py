from .clients.base import HttpClient


async def test_batch_graphql_query(http_client_class: type[HttpClient]):
    http_client = http_client_class(batch=True)

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
    http_client = http_client_class(batch=False)

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
