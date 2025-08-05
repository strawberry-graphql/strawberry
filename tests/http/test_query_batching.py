import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig
from tests.conftest import skip_if_gql_32
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, MyExtension, Query, Subscription


@pytest.fixture
def batching_http_client(http_client_class: type[HttpClient]) -> HttpClient:
    return http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 10}),
        )
    )


async def test_batching_works_with_multiple_queries(batching_http_client):
    response = await batching_http_client.post(
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


async def test_batching_works_with_single_query(batching_http_client):
    response = await batching_http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
    ]


async def test_variables_can_be_supplied_per_query(batching_http_client):
    response = await batching_http_client.post(
        url="/graphql",
        json=[
            {
                "query": "query InjectedVariables($name: String!) { hello(name: $name) }",
                "variables": {"name": "Alice"},
            },
            {
                "query": "query InjectedVariables($name: String!) { hello(name: $name) }",
                "variables": {"name": "Bob"},
            },
            {"query": "query NoVariables{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {"data": {"hello": "Hello Alice"}, "extensions": {"example": "example"}},
        {"data": {"hello": "Hello Bob"}, "extensions": {"example": "example"}},
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
    ]


async def test_operations_can_be_selected_per_query(batching_http_client):
    response = await batching_http_client.post(
        url="/graphql",
        json=[
            {
                "query": 'query Op1 { hello(name: "Op1") } query Op2 { hello(name: "Op2") }',
                "operationName": "Op1",
            },
            {
                "query": 'query Op1 { hello(name: "Op1") } query Op2 { hello(name: "Op2") }',
                "operationName": "Op2",
            },
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {"data": {"hello": "Hello Op1"}, "extensions": {"example": "example"}},
        {"data": {"hello": "Hello Op2"}, "extensions": {"example": "example"}},
    ]


@skip_if_gql_32("formatting is different in gql 3.2")
async def test_extensions_are_handled_per_query(batching_http_client):
    response = await batching_http_client.post(
        url="/graphql",
        json=[
            {
                "query": 'query { valueFromExtensions(key: "test") }',
                "extensions": {"test": "op1-value"},
            },
            {
                "query": 'query { valueFromExtensions(key: "test") }',
                "extensions": {"test": "op2-value"},
            },
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {
            "data": {"valueFromExtensions": "op1-value"},
            "extensions": {"example": "example"},
        },
        {
            "data": {"valueFromExtensions": "op2-value"},
            "extensions": {"example": "example"},
        },
    ]


async def test_context_is_shared_between_operations(batching_http_client):
    response = await batching_http_client.post(
        url="/graphql",
        json=[
            {"query": 'mutation { updateContext(key: "test", value: "shared-value") }'},
            {"query": 'query { valueFromContext(key: "test") }'},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {
            "data": {"updateContext": True},
            "extensions": {"example": "example"},
        },
        {
            "data": {"valueFromContext": "shared-value"},
            "extensions": {"example": "example"},
        },
    ]


async def test_returns_error_when_batching_is_disabled(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config=None),
        )
    )

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


async def test_returns_error_when_trying_too_many_operations(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 2}),
        )
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "Too many operations" in response.text
