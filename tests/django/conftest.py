from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, List

import pytest

if TYPE_CHECKING:
    from strawberry.django.test import GraphQLTestClient


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]):
    # automatically mark tests with 'django' if they are in the django subfolder

    rootdir = pathlib.Path(config.rootdir)

    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)

        if str(rel_path).startswith("tests/django"):
            item.add_marker(pytest.mark.django)


@pytest.fixture()
def graphql_client() -> GraphQLTestClient:
    from django.test.client import Client

    from strawberry.django.test import GraphQLTestClient

    return GraphQLTestClient(Client())
