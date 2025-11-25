import contextlib
from typing import Literal

import pytest

import strawberry
from strawberry.http.base import BaseView
from strawberry.schema.config import StrawberryConfig
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, MyExtension, Query, Subscription, schema


@pytest.fixture
def http_client(http_client_class: type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        import django

        if django.VERSION < (4, 2):
            pytest.skip(reason="Django < 4.2 doesn't async streaming responses")

        from tests.http.clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.skip(
                reason="(sync) DjangoHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.channels import SyncChannelsHttpClient

        # TODO: why do we have a sync channels client?
        if http_client_class is SyncChannelsHttpClient:
            pytest.skip(
                reason="SyncChannelsHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_flask import AsyncFlaskHttpClient
        from tests.http.clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.skip(
                reason="FlaskHttpClient doesn't support multipart subscriptions"
            )

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(
                reason="AsyncFlaskHttpClient doesn't support multipart subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(
                reason="ChaliceHttpClient doesn't support multipart subscriptions"
            )

    return http_client_class(schema=schema)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize(
    "accept_header",
    [
        pytest.param(
            "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
            id="with-boundary",
        ),
        pytest.param(
            'multipart/mixed;subscriptionSpec="1.0",application/json',
            id="no-boundary-with-quotes",
        ),
    ],
)
async def test_multipart_subscription(
    http_client: HttpClient, method: Literal["get", "post"], accept_header: str
):
    response = await http_client.query(
        method=method,
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": accept_header,
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


async def test_multipart_subscription_use_the_views_decode_json_method(
    http_client: HttpClient, mocker
):
    spy = mocker.spy(BaseView, "decode_json")

    response = await http_client.query(
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

    assert spy.call_count == 1


async def test_returns_error_when_trying_to_use_batching_with_multipart_subscriptions(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 10}),
        )
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
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
