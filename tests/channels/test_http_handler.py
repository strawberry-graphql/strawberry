import json
from typing import Any, Dict, Optional

import pytest

from channels.testing import HttpCommunicator
from strawberry.channels import GraphQLHTTPConsumer
from strawberry.channels.handlers.http_handler import SyncGraphQLHTTPConsumer
from tests.channels.schema import schema


def generate_body(query: str, variables: Optional[Dict[str, Any]] = None):
    body: Dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = variables

    return json.dumps(body).encode()


def generate_get_path(path, query: str, variables: Optional[Dict[str, Any]] = None):
    body: Dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = json.dumps(variables)

    parts = [f"{k}={v}" for k, v in body.items()]
    return f"{path}?{'&'.join(parts)}"


def assert_response(
    response: Dict[str, Any], expected: Any, errors: Optional[Any] = None
):
    assert response["status"] == 200
    body = json.loads(response["body"])
    assert "errors" not in body
    assert body["data"] == expected


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphiql_view(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        "/graphql",
        headers=[(b"accept", b"text/html")],
    )
    response = await client.get_response()
    assert response["headers"] == [(b"Content-Type", b"text/html")]
    assert response["status"] == 200
    assert b"GraphiQL" in response["body"]


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphiql_view_disabled(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema, graphiql=False),
        "GET",
        "/graphql",
        headers=[(b"accept", b"text/html")],
    )
    response = await client.get_response()
    assert response == {
        "headers": [(b"Allow", b"GET, POST")],
        "status": 405,
        "body": b"Method not allowed",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphiql_view_not_allowed(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        "/graphql",
    )
    response = await client.get_response()
    assert response == {
        "headers": [(b"Allow", b"GET, POST")],
        "status": 405,
        "body": b"Method not allowed",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
@pytest.mark.parametrize("method", ["DELETE", "HEAD", "PUT", "PATCH"])
async def test_disabled_methods(consumer, method: str):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        method,
        "/graphql",
        headers=[(b"accept", b"text/html")],
    )
    response = await client.get_response()
    assert response == {
        "headers": [(b"Allow", b"GET, POST")],
        "status": 405,
        "body": b"Method not allowed",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_fails_on_multipart_body(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=generate_body("{ hello }"),
        headers=[(b"content-type", b"multipart/form-data")],
    )
    response = await client.get_response()
    assert response == {
        "status": 500,
        "headers": [],
        "body": b"Unable to parse the multipart body",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
@pytest.mark.parametrize("body", [b"{}", b'{"foo": "bar"}'])
async def test_fails_on_missing_query(consumer, body: bytes):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=body,
    )
    response = await client.get_response()
    assert response == {
        "status": 500,
        "headers": [],
        "body": b"No GraphQL query found in the request",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
@pytest.mark.parametrize("body", [b"", b"definitely-not-json-string"])
async def test_fails_on_invalid_query(consumer, body: bytes):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=body,
    )
    response = await client.get_response()
    assert response == {
        "status": 500,
        "headers": [],
        "body": b"Unable to parse request body as JSON",
    }


@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_post_query_fails_using_params(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        "/graphql?foo=bar",
    )
    response = await client.get_response()
    assert response == {
        "status": 500,
        "headers": [],
        "body": b"No GraphQL query found in the request",
    }


# FIXME: All the tests bellow runs fine if running tests in this file only,
# but fail for Sync when running the whole testsuite, unless using.
# @pytest.mark.django_db. Probably because of the `database_sync_to_async`?


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_query(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=generate_body("{ hello }"),
    )
    assert_response(
        await client.get_response(),
        {"hello": "Hello world"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_can_pass_variables(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=generate_body(
            "query Hello($name: String!) { hello(name: $name) }",
            variables={"name": "James"},
        ),
    )
    assert_response(
        await client.get_response(),
        {"hello": "Hello James"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_get_query_using_params(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        generate_get_path("/graphql", "{ hello }"),
    )
    assert_response(
        await client.get_response(),
        {"hello": "Hello world"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_can_pass_variables_using_params(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        generate_get_path(
            "/graphql",
            "query Hello($name: String!) { hello(name: $name) }",
            variables={"name": "James"},
        ),
    )
    assert_response(
        await client.get_response(),
        {"hello": "Hello James"},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_returns_errors_and_data(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "POST",
        "/graphql",
        body=generate_body("{ hello, alwaysFail }"),
    )
    response = await client.get_response()
    assert response["status"] == 200
    assert json.loads(response["body"]) == {
        "data": {"alwaysFail": None, "hello": "Hello world"},
        "errors": [
            {
                "locations": [{"column": 10, "line": 1}],
                "message": "You are not authorized",
                "path": ["alwaysFail"],
            }
        ],
    }


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_get_does_not_allow_mutation(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema),
        "GET",
        generate_get_path("/graphql", "mutation { hello }"),
    )
    response = await client.get_response()
    assert response == {
        "status": 406,
        "headers": [],
        "body": b"mutations are not allowed when using GET",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("consumer", [GraphQLHTTPConsumer, SyncGraphQLHTTPConsumer])
async def test_graphql_get_not_allowed(consumer):
    client = HttpCommunicator(
        consumer.as_asgi(schema=schema, allow_queries_via_get=False),
        "GET",
        generate_get_path("/graphql", "query { hello }"),
    )
    response = await client.get_response()
    assert response == {
        "status": 406,
        "headers": [],
        "body": b"queries are not allowed when using GET",
    }
