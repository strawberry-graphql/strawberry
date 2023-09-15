from typing_extensions import Literal

import pytest

from .clients.base import HttpClient


@pytest.mark.parametrize("method", ["get", "post"])
async def test_graphql_query(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ hello }",
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["hello"] == "Hello world"


@pytest.mark.parametrize("method", ["get", "post"])
async def test_graphql_can_pass_variables(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query="query hello($name: String!) { hello(name: $name) }",
        variables={"name": "Jake"},
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["hello"] == "Hello Jake"


@pytest.mark.parametrize("method", ["get", "post"])
async def test_root_value(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ rootName }",
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["rootName"] == "Query"


@pytest.mark.parametrize("method", ["get", "post"])
async def test_passing_invalid_query(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query="{ h",
    )

    assert response.status_code == 200
    assert response.json["errors"] == [
        {
            "message": "Syntax Error: Expected Name, found <EOF>.",
            "locations": [{"line": 1, "column": 4}],
        }
    ]


@pytest.mark.parametrize("method", ["get", "post"])
async def test_returns_errors(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ maya }",
    )

    assert response.status_code == 200
    assert response.json["errors"] == [
        {
            "message": "Cannot query field 'maya' on type 'Query'.",
            "locations": [{"line": 1, "column": 3}],
        }
    ]


@pytest.mark.parametrize("method", ["get", "post"])
async def test_returns_errors_and_data(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query="{ hello, alwaysFail }",
    )

    assert response.status_code == 200
    data = response.json["data"]
    errors = response.json["errors"]

    assert errors == [
        {
            "locations": [{"column": 10, "line": 1}],
            "message": "You are not authorized",
            "path": ["alwaysFail"],
        }
    ]
    assert data == {"hello": "Hello world", "alwaysFail": None}


async def test_passing_invalid_json_post(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        data=b"{ h",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert "Unable to parse request body as JSON" in response.text


async def test_passing_invalid_json_get(http_client: HttpClient):
    response = await http_client.get(
        url="/graphql?query={ hello }&variables='{'",
    )

    assert response.status_code == 400
    assert "Unable to parse request body as JSON" in response.text


async def test_missing_query(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        json={},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert "No GraphQL query found in the request" in response.text


@pytest.mark.parametrize("method", ["get", "post"])
async def test_query_context(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ valueFromContext }",
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data["valueFromContext"] == "a value from context"


@pytest.mark.parametrize("method", ["get", "post"])
async def test_returning_status_code(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query="{ returns401 }",
    )

    assert response.status_code == 401
    assert response.json["data"] == {"returns401": "hey"}


@pytest.mark.parametrize("method", ["get", "post"])
async def test_updating_headers(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        variables={"name": "Jake"},
        query="query ($name: String!) { setHeader(name: $name) }",
    )

    assert response.status_code == 200
    assert response.json["data"] == {"setHeader": "Jake"}
    assert response.headers["X-Name"] == "Jake"


@pytest.mark.parametrize("method", ["get", "post"])
async def test_setting_cookie(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="query { setCookie }",
    )

    assert response.status_code == 200
    assert "errors" not in response.json
    assert "Set-Cookie" in response.headers
    assert "strawberry=rocks" in response.headers["Set-Cookie"]


@pytest.mark.parametrize("method", ["get", "post"])
async def test_setting_multiple_cookies(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query="query { setTwoCookies }",
    )

    assert response.status_code == 200
    assert "errors" not in response.json
    assert "Set-Cookie" in response.headers

    if hasattr(response.headers, "get_all"):
        headers = response.headers.get_all("Set-Cookie")
    elif hasattr(response.headers, "getall"):
        headers = response.headers.getall("Set-Cookie")
    elif hasattr(response.headers, "get_list"):
        headers = response.headers.get_list("Set-Cookie")
    else:
        headers = response.headers["Set-Cookie"]

    assert any(cookie_value.startswith("strawberry=rocks") for cookie_value in headers)
    assert any(cookie_value.startswith("snek=is_little") for cookie_value in headers)
