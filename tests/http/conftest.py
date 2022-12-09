from typing import Type

import pytest

from .clients import HttpClient
from .clients.starlite import StarliteHttpClient


@pytest.fixture(
    params=[
        # AioHttpClient,
        # AsgiHttpClient,
        # AsyncDjangoHttpClient,
        # AsyncFlaskHttpClient,
        # ChaliceHttpClient,
        # DjangoHttpClient,
        # FastAPIHttpClient,
        # FlaskHttpClient,
        # SanicHttpClient,
        StarliteHttpClient
    ]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()
