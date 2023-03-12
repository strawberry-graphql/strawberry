from typing import Type

import pytest

from ..http.clients import HttpClient
from ..http.clients.aiohttp import AioHttpClient
from ..http.clients.asgi import AsgiHttpClient
from ..http.clients.fastapi import FastAPIHttpClient


@pytest.fixture(
    params=[
        AioHttpClient,
        AsgiHttpClient,
        FastAPIHttpClient,
    ],
    ids=["aio", "asgi", "fastapi"]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class, event_loop) -> HttpClient:
    return http_client_class()
