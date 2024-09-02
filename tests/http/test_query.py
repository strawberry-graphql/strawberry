from typing_extensions import Literal

import pytest
from graphql import GraphQLError
from pytest_mock import MockFixture

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
async def test_calls_handle_errors(
    method: Literal["get", "post"], http_client: HttpClient, mocker: MockFixture
):
    sync_mock = mocker.patch(
        "strawberry.http.sync_base_view.SyncBaseHTTPView._handle_errors"
    )
    async_mock = mocker.patch(
        "strawberry.http.async_base_view.AsyncBaseHTTPView._handle_errors"
    )

    response = await http_client.query(
        method=method,
        query="{ hey }",
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert data is None

    assert response.json["errors"] == [
        {
            "message": "Cannot query field 'hey' on type 'Query'.",
            "locations": [{"line": 1, "column": 3}],
        }
    ]

    error = GraphQLError("Cannot query field 'hey' on type 'Query'.")

    response_data = {
        "data": None,
        "errors": [
            {
                "message": "Cannot query field 'hey' on type 'Query'.",
                "locations": [{"line": 1, "column": 3}],
            },
        ],
        "extensions": {"example": "example"},
    }

    call_args = async_mock.call_args[0] if async_mock.called else sync_mock.call_args[0]

    assert call_args[0][0].message == error.message
    assert call_args[1] == response_data


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


async def test_query_parameters_are_never_interpreted_as_list(http_client: HttpClient):
    response = await http_client.get(
        url='/graphql?query=query($name: String!) { hello(name: $name) }&variables={"name": "Jake"}&variables={"name": "Jake"}',
    )

    assert response.status_code == 200
    assert response.json["data"] == {"hello": "Hello Jake"}


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
    assert response.headers["x-name"] == "Jake"
