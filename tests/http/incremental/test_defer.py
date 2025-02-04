import contextlib
from typing_extensions import Literal

import pytest

from tests.http.clients.base import HttpClient


@pytest.mark.parametrize("method", ["get", "post"])
async def test_basic_defer(method: Literal["get", "post"], http_client: HttpClient):
    response = await http_client.query(
        method=method,
        query="""
        query HeroNameQuery {
            hero {
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

        assert initial == {
            "data": {"hero": {"id": "1"}},
            "hasNext": True,
            "pending": [{"path": ["hero"], "id": "0"}],
            # TODO: why is this None?
            "extensions": None,
        }

        subsequent = await stream.__anext__()

        assert subsequent == {
            "incremental": [
                {
                    "data": {"name": "Thiago Bellini"},
                    # TODO: we need to move these out of the data.
                    "extensions": {"example": "example"},
                }
            ],
            "completed": [{"id": "0"}],
            "hasNext": False,
            # TODO: fill from above
            "extensions": None,
        }
