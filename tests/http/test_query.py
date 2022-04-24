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


async def test_passing_invalid_query(http_client: HttpClient):
    response = await http_client.query(
        query="{ h",
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json["errors"] == [
        {
            "message": "Syntax Error: Expected Name, found <EOF>.",
            "locations": [{"line": 1, "column": 4}],
        }
    ]


async def test_passing_invalid_json(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        data=b"{ h",
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400
    assert "Unable to parse request body as JSON" in response.text


async def test_missing_query(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        json={},
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400
    # TODO: consolidate this
    assert (
        "No GraphQL query found in the request" in response.text
        or "No valid query was provided for the request" in response.text
    )
