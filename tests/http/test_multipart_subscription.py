import contextlib
from typing import Type

import pytest

from .clients.base import HttpClient


@pytest.fixture()
def http_client(http_client_class: Type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        from .clients.fastapi import FastAPIHttpClient

        if http_client_class is FastAPIHttpClient:
            # TODO: we could test this, but it doesn't make a lot of sense
            # we should fix httpx instead :)
            # https://github.com/encode/httpx/issues/2186
            pytest.xfail(reason="HTTPX doesn't support streaming yet")

    return http_client_class()


# TODO: do multipart subscriptions work on both GET and POST?
async def test_graphql_query(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        json={
            "query": 'subscription { echo(message: "Hello world", delay: 0.2) }',
        },
        headers={
            # TODO: this header might just be for django (the way it is written)
            "CONTENT_TYPE": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
        },
    )

    data = [d async for d in response.streaming_json()]

    assert data == [{"data": {"echo": "Hello world"}}]
