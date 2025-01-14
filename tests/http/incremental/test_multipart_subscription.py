from typing_extensions import Literal

import pytest

from strawberry.http.base import BaseView
from tests.http.clients.base import HttpClient


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
