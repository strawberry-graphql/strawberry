import contextlib

import pytest
from inline_snapshot import snapshot

from tests.http.clients.base import HttpClient


async def test_basic_stream(http_client: HttpClient):
    response = await http_client.query(
        method="get",
        query="""
        query Stream {
            streamableField @stream
        }
        """,
    )

    async with contextlib.aclosing(response.streaming_json()) as stream:
        initial = await stream.__anext__()

        assert initial == snapshot(
            {
                "data": {"streamableField": []},
                "hasNext": True,
                "pending": [{"id": "0", "path": ["streamableField"]}],
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
                        "path": ["streamableField"],
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
                        "path": ["streamableField"],
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
