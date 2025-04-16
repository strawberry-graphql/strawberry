import contextlib
from typing_extensions import Literal

import pytest
from inline_snapshot import snapshot

from tests.conftest import skip_if_gql_32
from tests.http.clients.base import HttpClient

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


async def test_basic_stream(http_client: HttpClient):
    response = await http_client.query(
        method="get",
        query="""
        query Stream {
            streambableField @stream
        }
        """,
    )

    async with contextlib.aclosing(response.streaming_json()) as stream:
        initial = await stream.__anext__()

        assert initial == snapshot(
            {
                "data": {"streambableField": []},
                "hasNext": True,
                "pending": [{"id": "0", "path": ["streambableField"]}],
                "extensions": None,
            }
        )

        first = await stream.__anext__()

        assert first == snapshot(
            {
                "hasNext": True,
                "extensions": None,
                "incremental": [
                    {
                        "items": ["Hello 0"],
                        "id": "0",
                        "path": ["streambableField"],
                        "label": None,
                    }
                ],
            }
        )

        second = await stream.__anext__()

        assert second == snapshot(
            {
                "hasNext": True,
                "extensions": None,
                "incremental": [
                    {
                        "items": ["Hello 1"],
                        "id": "0",
                        "path": ["streambableField"],
                        "label": None,
                    }
                ],
            }
        )

        third = await stream.__anext__()

        assert third == snapshot(
            {"hasNext": False, "extensions": None, "completed": [{"id": "0"}]}
        )

        with pytest.raises(StopAsyncIteration):
            await stream.__anext__()
