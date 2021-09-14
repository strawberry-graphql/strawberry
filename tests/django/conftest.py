import pytest

from django.test.client import Client

from tests.django.client import GraphQLTestClient


@pytest.fixture()
def graphql_client():
    yield GraphQLTestClient(Client())
