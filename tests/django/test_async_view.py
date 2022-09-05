import json

import pytest

from asgiref.sync import sync_to_async

import django
from django.core.exceptions import BadRequest, SuspiciousOperation
from django.test.client import RequestFactory
from django.utils.http import urlencode

import strawberry
from strawberry.django.views import AsyncGraphQLView as AsyncBaseGraphQLView

from .app.models import Example


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        django.VERSION < (3, 1),
        reason="Async views are only supported in Django >= 3.1",
    ),
]


@strawberry.type
class Query:
    hello: str = "strawberry"

    @strawberry.field
    async def hello_async(self) -> str:
        return "async strawberry"

    @strawberry.field
    async def example_async(self) -> str:
        def _get_name():
            return Example.objects.first().name

        get_name = sync_to_async(_get_name)

        return await get_name()


schema = strawberry.Schema(query=Query)


class AsyncGraphQLView(AsyncBaseGraphQLView):
    ...


async def test_async_graphql_query():
    query = "{ helloAsync }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = await AsyncGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["helloAsync"] == "async strawberry"


async def test_graphiql_view():
    factory = RequestFactory()

    request = factory.get("/graphql/", HTTP_ACCEPT="text/html")

    response = await AsyncGraphQLView.as_view(schema=schema)(request)
    body = response.content.decode()

    assert "GraphiQL" in body


async def test_async_graphql_get_query_using_params():
    params = {"query": "{ helloAsync }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    response = await AsyncGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["helloAsync"] == "async strawberry"


async def test_async_graphql_post_query_fails_using_params():
    params = {"query": "{ helloAsync }"}

    factory = RequestFactory()
    request = factory.post(
        "/graphql",
        **{"QUERY_STRING": urlencode(params, doseq=True)},
        content_type="application/x-www-form-urlencoded"
    )

    with pytest.raises(
        SuspiciousOperation, match="No GraphQL query found in the request"
    ):
        await AsyncGraphQLView.as_view(schema=schema)(request)


async def test_async_graphql_get_does_not_allow_mutation():
    params = {"query": "mutation { hello }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    with pytest.raises(BadRequest, match="mutations are not allowed when using GET"):
        await AsyncGraphQLView.as_view(schema=schema)(request)


async def test_async_graphql_get_does_get_when_disabled():
    params = {"query": "{ helloAsync }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    with pytest.raises(BadRequest, match="queries are not allowed when using GET"):
        await AsyncGraphQLView.as_view(schema=schema, allow_queries_via_get=False)(
            request
        )


@pytest.mark.parametrize("method", ["DELETE", "HEAD", "PUT", "PATCH"])
async def test_disabled_methods(method):
    factory = RequestFactory()

    rf = getattr(factory, method.lower())

    request = rf("/graphql/")

    response = await AsyncGraphQLView.as_view(schema=schema)(request)

    assert response.status_code == 405


async def test_fails_when_not_sending_query():
    factory = RequestFactory()

    request = factory.post("/graphql/")

    with pytest.raises(
        SuspiciousOperation, match="No GraphQL query found in the request"
    ):
        await AsyncGraphQLView.as_view(schema=schema)(request)


async def test_fails_when_request_body_has_invalid_json():
    factory = RequestFactory()

    request = factory.post(
        "/graphql/", "definitely-not-json-string", content_type="application/json"
    )

    with pytest.raises(
        SuspiciousOperation, match="Unable to parse request body as JSON"
    ):
        await AsyncGraphQLView.as_view(schema=schema, graphiql=False)(request)


@pytest.mark.django_db
async def test_async_graphql_query_model():
    prepare_db = sync_to_async(
        lambda: Example.objects.create(name="This is a demo async")
    )
    await prepare_db()

    query = "{ exampleAsync }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = await AsyncGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["exampleAsync"] == "This is a demo async"

    reset_db = sync_to_async(lambda: Example.objects.all().delete())
    await reset_db()
