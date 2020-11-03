import json
from typing import List

import pytest

from asgiref.sync import sync_to_async

import django
from django.test.client import RequestFactory

import strawberry
from strawberry.dataloader import DataLoader
from strawberry.django.views import AsyncGraphQLView

from .app.models import Example


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        django.VERSION < (3, 1),
        reason="Async views are only supported in Django >= 3.1",
    ),
]


def _prepare_db():
    ids = []

    for index in range(5):
        ids.append(Example.objects.create(name=f"This is a demo async {index}").id)

    return ids


@pytest.mark.django_db
async def test_fetch_data_from_db(mocker):
    def _sync_batch_load(keys):
        data = Example.objects.filter(id__in=keys)

        return list(data)

    prepare_db = sync_to_async(_prepare_db)
    batch_load = sync_to_async(_sync_batch_load)

    ids = await prepare_db()

    async def idx(keys) -> List[Example]:
        return await batch_load(keys)

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader)

    @strawberry.type
    class Query:
        hello: str = "strawberry"

        @strawberry.field
        async def get_example(self, id: strawberry.ID) -> str:
            example = await loader.load(id)

            return example.name

    schema = strawberry.Schema(query=Query)

    query = f"""{{
        a: getExample(id: "{ids[0]}")
        b: getExample(id: "{ids[1]}")
        c: getExample(id: "{ids[2]}")
        d: getExample(id: "{ids[3]}")
        e: getExample(id: "{ids[4]}")
    }}"""

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = await AsyncGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert data["data"] == {
        "a": "This is a demo async 0",
        "b": "This is a demo async 1",
        "c": "This is a demo async 2",
        "d": "This is a demo async 3",
        "e": "This is a demo async 4",
    }

    reset_db = sync_to_async(lambda: Example.objects.all().delete())
    await reset_db()

    mock_loader.assert_called_once_with([str(id_) for id_ in ids])
