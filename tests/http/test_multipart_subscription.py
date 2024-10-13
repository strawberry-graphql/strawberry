import contextlib
from typing import Type
from typing_extensions import Literal

import pytest

from .clients.base import HttpClient


@pytest.fixture()
def http_client(http_client_class: Type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        import django

        if django.VERSION < (4, 2):
            pytest.skip(reason="Django < 4.2 doesn't async streaming responses")

        from .clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.skip(
                reason="(sync) DjangoHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from .clients.channels import SyncChannelsHttpClient

        # TODO: why do we have a sync channels client?
        if http_client_class is SyncChannelsHttpClient:
            pytest.skip(
                reason="SyncChannelsHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from .clients.async_flask import AsyncFlaskHttpClient
        from .clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.skip(
                reason="FlaskHttpClient doesn't support multipart subscriptions"
            )

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(
                reason="AsyncFlaskHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from .clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(
                reason="ChaliceHttpClient doesn't support multipart subscriptions"
            )

    return http_client_class()


@pytest.mark.parametrize("method", ["get", "post"])
async def test_multipart_subscription(
    http_client: HttpClient, method: Literal["get", "post"]
):
    response = await http_client.query(
        method=method,
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
            "content-type": "application/json",
        },
    )

    data = [d async for d in response.streaming_json()]

    assert data == [
        {
            "payload": {
                "data": {"echo": "Hello world"},
                "extensions": {"example": "example"},
            }
        }
    ]

    assert response.status_code == 200
