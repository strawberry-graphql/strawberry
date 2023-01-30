from typing import TYPE_CHECKING

from . import IS_STARLITE_INSTALLED
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

if TYPE_CHECKING:
    from typing import Any, Dict, Type

    import pytest


_clients_dict: "Dict[Type[HttpClient], Any]" = {
    AioHttpClient: pytest.param(AioHttpClient, marks=pytest.mark.aiohttp),
    AsgiHttpClient: pytest.param(AsgiHttpClient, marks=pytest.mark.asgi),
    AsyncDjangoHttpClient: pytest.param(
        AsyncDjangoHttpClient, marks=pytest.mark.django
    ),
    AsyncFlaskHttpClient: pytest.param(AsyncFlaskHttpClient, marks=pytest.mark.flask),
    ChaliceHttpClient: pytest.param(ChaliceHttpClient, marks=pytest.mark.chalice),
    DjangoHttpClient: pytest.param(DjangoHttpClient, marks=pytest.mark.django),
    FastAPIHttpClient: pytest.param(FastAPIHttpClient, marks=pytest.mark.fastapi),
    FlaskHttpClient: pytest.param(FlaskHttpClient, marks=pytest.mark.flask),
    SanicHttpClient: pytest.param(SanicHttpClient, marks=pytest.mark.sanic),
}


def pytest_generate_tests(metafunc: "pytest.Metafunc") -> None:
    if "http_client_class" in metafunc.fixturenames and IS_STARLITE_INSTALLED:
        from .clients.starlite import StarliteHttpClient

        _clients_dict[StarliteHttpClient] = pytest.param(
            StarliteHttpClient, marks=pytest.mark.starlite
        )

    metafunc.parametrize("http_client_class", _clients_dict.values())


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()
