import json

import pytest

from asgiref.sync import sync_to_async

import django
from django.core.exceptions import SuspiciousOperation
from django.test.client import RequestFactory

import strawberry
from strawberry.dataloader import DataLoader
from strawberry.django.dataloader import create_model_load_fn
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


@sync_to_async
def set_connection_debug(value: bool):
    from django.db import connection
    connection.force_debug_cursor = value


@pytest.mark.django_db
async def test_async_dataloader(django_assert_num_queries):
    @sync_to_async
    def prepare_db():
        for i in range(1, 4):
            e = Example.objects.create(name=f"This is number {i}")
            # Override ID
            e.id = i
            e.save()

    await prepare_db()

    class CustomView(AsyncBaseGraphQLView):
        async def get_context(self, *args, **kwargs):
            context = await super().get_context(*args, **kwargs)
            context.dataloaders = {
                "example_loader": DataLoader(load_fn=create_model_load_fn(Example))
            }
            return context

    @strawberry.type
    class Query:
        @strawberry.field
        async def get_example(self, info, id: int) -> str:
            loader = info.context.dataloaders["example_loader"]
            inst = await loader.load(id)
            return inst.name

    schema = strawberry.Schema(query=Query, extensions=[SyncToAsync])

    query = """
        {
            example1: getExample(id: 1)
            example2: getExample(id: 2)
            example3: getExample(id: 3)
        }
    """

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    await set_connection_debug(True)

    response = await CustomView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    @sync_to_async
    def get_queries():
        from django.db import connection
        return connection.queries

    assert len(await get_queries()) == 1
    await set_connection_debug(False)

    assert "errors" not in data
    assert data["data"] == {
        "example1": "This is number 1",
        "example2": "This is number 2",
        "example3": "This is number 3",
    }

    reset_db = sync_to_async(lambda: Example.objects.all().delete())
    await reset_db()
