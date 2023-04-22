from typing import Type

import pytest

from ..http.clients import (
    AioHttpClient,
    AsgiHttpClient,
    ChannelsHttpClient,
    FastAPIHttpClient,
    HttpClient,
    StarliteHttpClient,
)

clients = [
    AioHttpClient,
    AsgiHttpClient,
    FastAPIHttpClient,
    ChannelsHttpClient,
]
ids = ["aio", "asgi", "fastapi", "channels"]
if StarliteHttpClient:
    clients.append(StarliteHttpClient)
    ids.append("starlite")


@pytest.fixture(
    params=clients,
    ids=ids,
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class, event_loop) -> HttpClient:
    return http_client_class()
