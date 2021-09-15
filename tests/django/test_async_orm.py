import json

import pytest

from asgiref.sync import sync_to_async

import django
from django.core.exceptions import SuspiciousOperation
from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import AsyncGraphQLView as AsyncBaseGraphQLView
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
