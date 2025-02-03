import contextlib

import pytest

from tests.http.clients.base import HttpClient


@pytest.fixture
def http_client(http_client_class: type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        import django

        if django.VERSION < (4, 2):
            pytest.skip(reason="Django < 4.2 doesn't async streaming responses")

        from tests.http.clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.skip(reason="(sync) DjangoHttpClient doesn't support streaming")

    with contextlib.suppress(ImportError):
        from tests.http.clients.channels import SyncChannelsHttpClient

        # TODO: why do we have a sync channels client?
        if http_client_class is SyncChannelsHttpClient:
            pytest.skip(reason="SyncChannelsHttpClient doesn't support streaming")

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_flask import AsyncFlaskHttpClient
        from tests.http.clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.skip(reason="FlaskHttpClient doesn't support streaming")

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(reason="AsyncFlaskHttpClient doesn't support streaming")

    with contextlib.suppress(ImportError):
        from tests.http.clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(reason="ChaliceHttpClient doesn't support streaming")

    return http_client_class()
