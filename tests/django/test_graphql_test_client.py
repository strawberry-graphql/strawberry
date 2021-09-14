def test_query(graphql_client):
    query = """query {
        user
    }
    """

    result = graphql_client.query(query)

    assert result.data["user"] == "🍓"
