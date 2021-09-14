from django.test.client import Client

from tests.django.client import GraphQLTestClient


def test_query():
    query = """query {
        user
    }
    """

    result = GraphQLTestClient(Client()).query(query)

    assert result.errors is None
    assert result.data["user"] == "🍓"
