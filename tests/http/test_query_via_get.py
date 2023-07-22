from .clients.base import HttpClient


async def test_sending_empty_query(http_client_class):
    http_client = http_client_class()

    response = await http_client.query(
        method="get", query="", variables={"fake": "variable"}
    )

    assert response.status_code == 400
    assert "No GraphQL query found in the request" in response.text


async def test_does_not_allow_mutation(http_client: HttpClient):
    response = await http_client.query(method="get", query="mutation { hello }")

    assert response.status_code == 400
    assert "mutations are not allowed when using GET" in response.text


async def test_fails_if_allow_queries_via_get_false(http_client_class):
    http_client = http_client_class(allow_queries_via_get=False)

    response = await http_client.query(method="get", query="{ hello }")

    assert response.status_code == 400
    assert "queries are not allowed when using GET" in response.text
