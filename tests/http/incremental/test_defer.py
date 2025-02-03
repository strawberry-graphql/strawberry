import contextlib
from typing_extensions import Literal

import pytest

from tests.http.clients.base import HttpClient


@pytest.mark.parametrize("method", ["get", "post"])
async def test_basic_defer(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="""{
            hello

            ... @defer {
                asyncHello
            }
        }""",
    )

    async with contextlib.aclosing(response.streaming_json()) as stream:
        initial = await stream.__anext__()

        assert initial == {
            "data": {"hello": "Hello world"},
            "incremental": [],
            "hasNext": True,
            # TODO: why is this None?
            "extensions": None,
        }

        subsequent = await stream.__anext__()

        assert subsequent == {
            "incremental": [
                {
                    "data": {"asyncHello": "Hello world"},
                    "extensions": {"example": "example"},
                }
            ],
            "hasNext": False,
            # TODO: how do we fill these?
            "extensions": None,
        }
