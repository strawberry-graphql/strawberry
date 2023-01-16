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
from .clients.starlite import StarliteHttpClient


@pytest.fixture(
    params=[
        pytest.param(AioHttpClient, marks=pytest.mark.aiohttp),
        pytest.param(AsgiHttpClient, marks=pytest.mark.asgi),
        pytest.param(AsyncDjangoHttpClient, marks=pytest.mark.django),
        pytest.param(AsyncFlaskHttpClient, marks=pytest.mark.flask),
        pytest.param(ChaliceHttpClient, marks=pytest.mark.chalice),
        pytest.param(DjangoHttpClient, marks=pytest.mark.django),
        pytest.param(FastAPIHttpClient, marks=pytest.mark.fastapi),
        pytest.param(FlaskHttpClient, marks=pytest.mark.flask),
        pytest.param(SanicHttpClient, marks=pytest.mark.sanic),
        pytest.param(StarliteHttpClient, marks=pytest.mark.starlite),
    ]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()
