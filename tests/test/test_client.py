"""Test that assert_no_errors includes response.errors in the AssertionError message."""

from contextlib import nullcontext
from typing import Any

import pytest

from strawberry.utils.await_maybe import await_maybe

query_to_non_existent_field = "{ nonExistentField { id } }"


def check_non_existent_field_error(errors: Any):
    assert isinstance(errors, list)
    assert len(errors) == 1
    error = errors[0]
    assert isinstance(error, dict)
    assert "nonExistentField" in error["message"]
    assert "Cannot query field" in error["message"]
    assert error["locations"]


@pytest.mark.parametrize(
    ("assert_no_errors", "expectation"),
    [(True, pytest.raises(AssertionError)), (False, nullcontext())],
)
async def test_query_with_assert_no_errors_option(
    graphql_client, assert_no_errors, expectation
):
    query = "{ ThisIsNotAValidQuery }"

    with expectation:
        await await_maybe(
            graphql_client.query(query, assert_no_errors=assert_no_errors)
        )


@pytest.mark.asgi
def test_asgi_client_assert_no_errors_verbose_message():
    from starlette.testclient import TestClient

    from strawberry.asgi import GraphQL
    from strawberry.asgi.test import GraphQLTestClient
    from tests.views.schema import schema

    client = GraphQLTestClient(TestClient(GraphQL(schema)))

    with pytest.raises(AssertionError) as exc_info:
        client.query(query_to_non_existent_field)

    check_non_existent_field_error(exc_info.value.args[0])


def test_graphql_test_client_assert_no_errors_verbose_message():
    from strawberry.test.client import GraphQLTestClient
    from tests.views.schema import schema

    client = GraphQLTestClient(schema)

    with pytest.raises(AssertionError) as exc_info:
        client.query(query_to_non_existent_field)

    check_non_existent_field_error(exc_info.value.args[0])


@pytest.mark.django
def test_django_client_assert_no_errors_verbose_message():
    from django.test.client import Client

    from strawberry.django.test import GraphQLTestClient

    client = GraphQLTestClient(Client())

    with pytest.raises(AssertionError) as exc_info:
        client.query(query_to_non_existent_field)

    check_non_existent_field_error(exc_info.value.args[0])


@pytest.mark.aiohttp
async def test_aiohttp_client_assert_no_errors_verbose_message():
    try:
        from aiohttp import web
        from aiohttp.test_utils import TestClient as AiohttpTestClient
        from aiohttp.test_utils import TestServer

        from strawberry.aiohttp.test import GraphQLTestClient
        from strawberry.aiohttp.views import GraphQLView
    except ImportError:
        pytest.skip("Aiohttp not installed")

    from tests.views.schema import schema

    view = GraphQLView(schema=schema)
    app = web.Application()
    app.router.add_route("*", "/graphql/", view)

    async with AiohttpTestClient(TestServer(app)) as client:
        graphql_client = GraphQLTestClient(client)

        with pytest.raises(AssertionError) as exc_info:
            await graphql_client.query(query_to_non_existent_field)

        check_non_existent_field_error(exc_info.value.args[0])
