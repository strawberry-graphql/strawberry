import json

import pytest

from asgiref.sync import sync_to_async

import django
from django.test.client import RequestFactory
from django.db import transaction

import strawberry
from strawberry.django.views import (
    AsyncGraphQLView as AsyncBaseGraphQLView,
    GraphQLView,
)
from strawberry.extensions import Extension
from strawberry.extensions.sync_to_async import SyncToAsync

from .app.models import Example


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        django.VERSION < (3, 1),
        reason="Async views are only supported in Django >= 3.1",
    ),
]


class AsyncGraphQLView(AsyncBaseGraphQLView):
    ...


@pytest.mark.django_db
async def test_async_sync_to_async():
    prepare_db = sync_to_async(
        lambda: Example.objects.create(name="This is a demo async")
    )
    await prepare_db()

    @strawberry.type
    class Query:
        @strawberry.field
        def example_async(self) -> str:
            return Example.objects.first().name

    schema = strawberry.Schema(query=Query, extensions=[SyncToAsync])

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


@pytest.mark.django_db
async def test_sync_to_async_with_transaction():
    prepare_db = sync_to_async(
        lambda: Example.objects.create(name="This is a demo async")
    )
    await prepare_db()

    @strawberry.type
    class Query:
        @strawberry.field
        def example_async(self) -> str:
            with transaction.atomic():
                return Example.objects.first().name

    schema = strawberry.Schema(query=Query, extensions=[SyncToAsync])

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


@pytest.mark.django_db
async def test_sync_to_async_with_request_transaction():
    prepare_db = sync_to_async(
        lambda: Example.objects.create(name="This is a demo async")
    )
    await prepare_db()

    class WrapRequestInTransaction(Extension):
        @sync_to_async
        def on_request_start(self):
            transaction.atomic().__enter__()

        @sync_to_async
        def on_request_end(self):
            transaction.atomic().__exit__(None, None, None)

    @strawberry.type
    class Query:
        @strawberry.field
        def example_async(self) -> str:
            return Example.objects.first().name

    schema = strawberry.Schema(
        query=Query, extensions=[SyncToAsync, WrapRequestInTransaction]
    )

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


@pytest.mark.django_db
def test_sync_to_async_works_in_sync_context():
    Example.objects.create(name="This is a demo async")

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return Example.objects.first().name

    schema = strawberry.Schema(query=Query, extensions=[SyncToAsync])

    query = "{ example }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["example"] == "This is a demo async"

    Example.objects.all().delete()
