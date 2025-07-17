import contextlib
from typing_extensions import Literal

import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.extensions.mask_errors import MaskErrors
from strawberry.schema.config import StrawberryConfig
from tests.conftest import skip_if_gql_32
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, Query, Subscription

pytestmark = skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")


@pytest.mark.parametrize("method", ["get", "post"])
async def test_basic_defer(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="""
        query HeroNameQuery {
            character {
                id
                ...NameFragment @defer
            }
        }
        fragment NameFragment on Hero {
            name
        }
        """,
    )

    async with contextlib.aclosing(response.streaming_json()) as stream:
        initial = await stream.__anext__()

        assert initial == snapshot(
            {
                "data": {"character": {"id": "1"}},
                "hasNext": True,
                "pending": [{"path": ["character"], "id": "0"}],
                # TODO: check if we need this and how to handle it
                "extensions": None,
            }
        )

        subsequent = await stream.__anext__()

        assert subsequent == snapshot(
            {
                "incremental": [
                    {
                        "data": {"name": "Thiago Bellini"},
                        "id": "0",
                        "path": ["character"],
                        "label": None,
                    }
                ],
                "completed": [{"id": "0"}],
                "hasNext": False,
                # TODO: same as above
                "extensions": None,
            }
        )


@pytest.mark.parametrize("method", ["get", "post"])
async def test_defer_with_mask_error_extension(
    method: Literal["get", "post"], incremental_http_client_class: type[HttpClient]
):
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        extensions=[MaskErrors()],
        config=StrawberryConfig(enable_experimental_incremental_execution=(True)),
    )

    http_client = incremental_http_client_class(schema=schema)
    response = await http_client.query(
        method=method,
        query="""
        query HeroNameQuery {
            character {
                id
                ...NameFragment @defer
            }
        }
        fragment NameFragment on Hero {
            name(fail: true)
        }
        """,
    )

    async with contextlib.aclosing(response.streaming_json()) as stream:
        initial = await stream.__anext__()

        assert initial == snapshot(
            {
                "data": {"character": {"id": "1"}},
                "hasNext": True,
                "pending": [{"path": ["character"], "id": "0"}],
                # TODO: check if we need this and how to handle it
                "extensions": None,
            }
        )

        subsequent = await stream.__anext__()

        assert subsequent == snapshot(
            {
                "incremental": [
                    {
                        "data": {"name": "Thiago Bellini"},
                        "id": "0",
                        "path": ["character"],
                        "label": None,
                    }
                ],
                "completed": [{"id": "0"}],
                "hasNext": False,
                # TODO: same as above
                "extensions": None,
            }
        )
