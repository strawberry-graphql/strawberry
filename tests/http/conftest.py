import importlib
from typing import Any, Generator, Type

import pytest

from .clients.base import HttpClient


def _get_http_client_classes() -> Generator[Any, None, None]:
    for client, module, marks in [
        ("AioHttpClient", "aiohttp", [pytest.mark.aiohttp]),
        ("AsgiHttpClient", "asgi", [pytest.mark.asgi]),
        ("AsyncDjangoHttpClient", "async_django", [pytest.mark.django]),
        ("AsyncFlaskHttpClient", "async_flask", [pytest.mark.flask]),
        ("ChannelsHttpClient", "channels", [pytest.mark.channels]),
        ("ChaliceHttpClient", "chalice", [pytest.mark.chalice]),
        ("DjangoHttpClient", "django", [pytest.mark.django]),
        ("FastAPIHttpClient", "fastapi", [pytest.mark.fastapi]),
        ("FlaskHttpClient", "flask", [pytest.mark.flask]),
        ("SanicHttpClient", "sanic", [pytest.mark.sanic]),
        ("StarliteHttpClient", "starlite", [pytest.mark.starlite]),
        (
            "SyncChannelsHttpClient",
            "channels",
            [pytest.mark.channels, pytest.mark.django_db],
        ),
    ]:
        try:
            client_class = getattr(
                importlib.import_module(f".{module}", package="tests.http.clients"),
                client,
            )
        except ImportError:
            client_class = None

        yield pytest.param(
            client_class,
            marks=[
                *marks,
                pytest.mark.skipif(
                    client_class is None, reason=f"Client {client} not found"
                ),
            ],
        )


@pytest.fixture(params=_get_http_client_classes())
def http_client_class(request: Any) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class: Type[HttpClient]) -> HttpClient:
    return http_client_class()
