def test_query(graphql_client):
    query = """query {
        hello
    }
    """

    result = graphql_client.query(query)

    assert result.data["hello"] == "🍓"
