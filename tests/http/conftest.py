from typing import Type

import pytest

from .clients import HttpClient
from .clients.aiohttp import AioHttpClient
from .clients.asgi import AsgiHttpClient
from .clients.async_django import AsyncDjangoHttpClient
from .clients.async_flask import AsyncFlaskHttpClient
from .clients.chalice import ChaliceHttpClient
from .clients.django import DjangoHttpClient
from .clients.fastapi import FastAPIHttpClient
from .clients.flask import FlaskHttpClient
from .clients.sanic import SanicHttpClient


@pytest.fixture(
    params=[
        AioHttpClient,
        AsgiHttpClient,
        AsyncDjangoHttpClient,
        AsyncFlaskHttpClient,
        ChaliceHttpClient,
        DjangoHttpClient,
        FastAPIHttpClient,
        FlaskHttpClient,
        SanicHttpClient,
    ]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()
