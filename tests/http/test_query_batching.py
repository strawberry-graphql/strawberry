import contextlib

import pytest

from .clients.base import HttpClient


@pytest.fixture
def multipart_subscriptions_batch_http_client(
    http_client_class: type[HttpClient],
) -> HttpClient:
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

    return http_client_class(batch=True)


async def test_batch_graphql_query(http_client_class: type[HttpClient]):
    http_client = http_client_class(batch=True)

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json == [
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
        {"data": {"hello": "Hello world"}, "extensions": {"example": "example"}},
    ]


async def test_returns_error_when_batching_is_disabled(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(batch=False)

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400

    assert "Batching is not enabled" in response.text


async def test_returns_error_for_multipart_subscriptions(
    multipart_subscriptions_batch_http_client: HttpClient,
):
    response = await multipart_subscriptions_batch_http_client.post(
        url="/graphql",
        json=[
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
        ],
        headers={
            "content-type": "application/json",
            "accept": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
        },
    )

    assert response.status_code == 400

    assert "Batching is not supported for multipart subscriptions" in response.text
