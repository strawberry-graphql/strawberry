from django.test.client import Client

from strawberry.django.test.client import GraphQLTestClient


def test_query():
    query = """query {
        user
    }
    """

    result = GraphQLTestClient(Client()).query(query)

    assert result.errors is None
