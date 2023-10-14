import contextlib
from typing import Type

import pytest

from .clients.base import HttpClient


@pytest.fixture()
def http_client(http_client_class: Type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        from .clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.xfail(reason="(sync) DjangoHttpClient doesn't support subscriptions")

    with contextlib.suppress(ImportError):
        from .clients.channels import SyncChannelsHttpClient

        # TODO: why do we have a sync channels client?
        if http_client_class is SyncChannelsHttpClient:
            pytest.xfail(reason="SyncChannelsHttpClient doesn't support subscriptions")

    with contextlib.suppress(ImportError):
        from .clients.async_flask import AsyncFlaskHttpClient
        from .clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.xfail(reason="FlaskHttpClient doesn't support subscriptions")

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(reason="AsyncFlaskHttpClient doesn't support subscriptions")

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
