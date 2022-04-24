from .clients import HttpClient


async def test_graphql_query(http_client: HttpClient):
    response = await http_client.query(
        query="{ hello }",
        headers={
            "Content-Type": "application/json",
        },
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["hello"] == "Hello world"


async def test_graphql_can_pass_variables(http_client: HttpClient):
    response = await http_client.query(
        query="query hello($name: String!) { hello(name: $name) }",
        variables={"name": "Jake"},
        headers={
            "Content-Type": "application/json",
        },
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["hello"] == "Hello Jake"
