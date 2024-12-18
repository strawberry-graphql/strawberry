import json

import pytest
from asgiref.sync import sync_to_async
from pytest_mock import MockerFixture

import strawberry
from strawberry.dataloader import DataLoader

try:
    import django

    DJANGO_VERSION: tuple[int, int, int] = django.VERSION
except ImportError:
    DJANGO_VERSION = (0, 0, 0)


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        DJANGO_VERSION < (3, 1),
        reason="Async views are only supported in Django >= 3.1",
    ),
]


def _prepare_db():
    from .app.models import Example

    return [
        Example.objects.create(name=f"This is a demo async {index}").pk
        for index in range(5)
    ]


@pytest.mark.django
@pytest.mark.django_db
async def test_fetch_data_from_db(mocker: MockerFixture):
    from django.test.client import RequestFactory

    from strawberry.django.views import AsyncGraphQLView

    from .app.models import Example

    def _sync_batch_load(keys: list[str]):
        data = Example.objects.filter(id__in=keys)

        return list(data)

    prepare_db = sync_to_async(_prepare_db)
    batch_load = sync_to_async(_sync_batch_load)

    ids = await prepare_db()

    async def idx(keys: list[str]) -> list[Example]:
        return await batch_load(keys)

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader[str, Example](load_fn=mock_loader)

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
