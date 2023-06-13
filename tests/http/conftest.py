import sys
from typing import Type

import pytest

from .clients import (
    AioHttpClient,
    AsgiHttpClient,
    AsyncDjangoHttpClient,
    AsyncFlaskHttpClient,
    ChaliceHttpClient,
    ChannelsHttpClient,
    DjangoHttpClient,
    FastAPIHttpClient,
    FlaskHttpClient,
    HttpClient,
    SanicHttpClient,
    StarliteHttpClient,
    SyncChannelsHttpClient,
)


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
        pytest.param(ChannelsHttpClient, marks=pytest.mark.channels),
        pytest.param(
            # SyncChannelsHttpClient uses @database_sync_to_async and therefore
            # needs pytest.mark.django_db
            SyncChannelsHttpClient,
            marks=[pytest.mark.channels, pytest.mark.django_db],
        ),
        pytest.param(
            StarliteHttpClient,
            marks=[
                pytest.mark.starlite,
                pytest.mark.skipif(
                    sys.version_info < (3, 8), reason="Starlite requires Python 3.8+"
                ),
            ],
        ),
    ]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()
