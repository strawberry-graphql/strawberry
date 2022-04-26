from .clients import HttpClient


async def test_does_not_allow_mutation(http_client: HttpClient):
    response = await http_client.query(method="get", query="mutation { hello }")

    assert response.status_code == 400
    assert "mutations are not allowed when using GET" in response.text


async def test_fails_if_allow_queries_via_get_false(http_client_class):
    http_client = http_client_class(allow_queries_via_get=False)

    response = await http_client.query(method="get", query="{ hello }")

    assert response.status_code == 400
    assert "queries are not allowed when using GET" in response.text
