def test_query(graphql_client):
    query = """query {
        hello
    }
    """

    result = graphql_client.query(query)

    assert result.data["hello"] == "🍓"


def test_query_variables(graphql_client):
    query = """query Hi($name: String!) {
        hi(name: $name)
    }
    """

    result = graphql_client.query(query, variables={"name": "Marcotte"})

    assert result.data == {"hi": "Hi Marcotte!"}
