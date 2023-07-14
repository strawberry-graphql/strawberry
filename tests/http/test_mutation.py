from .clients.base import HttpClient


async def test_mutation(http_client: HttpClient):
    response = await http_client.query(
        query="mutation { hello }",
        headers={
            "Content-Type": "application/json",
        },
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["hello"] == "strawberry"
