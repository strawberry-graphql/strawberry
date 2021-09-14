import pytest

from django.test.client import Client

from strawberry.django.client import GraphQLTestClient


@pytest.fixture()
def graphql_client():
    yield GraphQLTestClient(Client())
