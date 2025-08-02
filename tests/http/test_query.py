from typing_extensions import Literal

import pytest
from graphql import GraphQLError
from pytest_mock import MockFixture

from tests.conftest import skip_if_gql_32

from .clients.base import HttpClient


@pytest.mark.parametrize("method", ["get", "post"])
async def test_graphql_query(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ hello }",
    )
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
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
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["hello"] == "Hello Jake"


@pytest.mark.parametrize("extra_kwargs", [{"variables": None}, {}])
async def test_operation_variables_may_be_null_or_omitted(
    http_client: HttpClient, extra_kwargs
):
    response = await http_client.query(
        query="{ __typename }",
        **extra_kwargs,
    )
    data = response.json["data"]

    assert response.status_code == 200
    assert isinstance(data, dict)
    assert data["__typename"] == "Query"


@pytest.mark.parametrize(
    "not_an_object_or_null",
    ["string", 0, False, ["array"]],
)
async def test_requests_with_invalid_variables_parameter_are_rejected(
    http_client: HttpClient, not_an_object_or_null
):
    response = await http_client.query(
        query="{ __typename }",
        variables=not_an_object_or_null,
    )

    assert response.status_code == 400
    assert (
        response.data
        == b"The GraphQL operation's `variables` must be an object or null, if provided."
    )


@pytest.mark.parametrize("method", ["get", "post"])
async def test_root_value(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ rootName }",
    )
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
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


@pytest.mark.parametrize(
    "not_stringified_json",
    [{"obj": "ect"}, 0, False, ["array"]],
)
async def test_requests_with_invalid_query_parameter_are_rejected(
    http_client: HttpClient, not_stringified_json
):
    response = await http_client.query(
        query=not_stringified_json,
    )

    assert response.status_code == 400
    assert (
        response.data
        == b"The GraphQL operation's `query` must be a string or null, if provided."
    )


@pytest.mark.parametrize("method", ["get", "post"])
async def test_query_context(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="{ valueFromContext }",
    )
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["valueFromContext"] == "a value from context"


@skip_if_gql_32("formatting is different in gql 3.2")
@pytest.mark.parametrize("method", ["get", "post"])
async def test_query_extensions(
    method: Literal["get", "post"], http_client: HttpClient
):
    response = await http_client.query(
        method=method,
        query='{ valueFromExtensions(key:"test") }',
        extensions={"test": "hello"},
    )
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["valueFromExtensions"] == "hello"


@pytest.mark.parametrize(
    "not_an_object_or_null",
    ["string", 0, False, ["array"]],
)
async def test_requests_with_invalid_extension_parameter_are_rejected(
    http_client: HttpClient, not_an_object_or_null
):
    response = await http_client.query(
        query="{ __typename }",
        extensions=not_an_object_or_null,
    )

    assert response.status_code == 400
    assert (
        response.data
        == b"The GraphQL operation's `extensions` must be an object or null, if provided."
    )


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


@pytest.mark.parametrize(
    ("extra_kwargs", "expected_message"),
    [
        ({}, "Hello Foo"),
        ({"operation_name": None}, "Hello Foo"),
        ({"operation_name": "Query1"}, "Hello Foo"),
        ({"operation_name": "Query2"}, "Hello Bar"),
    ],
)
async def test_operation_selection(
    http_client: HttpClient, extra_kwargs, expected_message
):
    response = await http_client.query(
        query="""
            query Query1 { hello(name: "Foo") }
            query Query2 { hello(name: "Bar") }
        """,
        **extra_kwargs,
    )

    assert response.status_code == 200
    assert response.json["data"] == {"hello": expected_message}


@pytest.mark.parametrize(
    "operation_name",
    ["", "Query3"],
)
async def test_invalid_operation_selection(http_client: HttpClient, operation_name):
    response = await http_client.query(
        query="""
            query Query1 { hello(name: "Foo") }
            query Query2 { hello(name: "Bar") }
        """,
        operation_name=operation_name,
    )

    assert response.status_code == 400
    assert response.data == f'Unknown operation named "{operation_name}".'.encode()


async def test_operation_selection_without_operations(http_client: HttpClient):
    response = await http_client.query(
        query="""
            fragment Fragment1 on Query { __typename }
        """,
    )

    assert response.status_code == 400
    assert response.data == b"Can't get GraphQL operation type"
