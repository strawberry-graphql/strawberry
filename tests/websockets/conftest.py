from typing import Type

import pytest

from ..http.clients import (
    AioHttpClient,
    AsgiHttpClient,
    ChannelsHttpClient,
    FastAPIHttpClient,
    HttpClient,
)


@pytest.fixture(
    params=[
        AioHttpClient,
        AsgiHttpClient,
        FastAPIHttpClient,
        ChannelsHttpClient,
    ],
    ids=["aio", "asgi", "fastapi", "channels"],
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class, event_loop) -> HttpClient:
    return http_client_class()
