def test_query(graphql_client):
    query = """query {
        user
    }
    """

    result = graphql_client.query(query)

    assert result.data["user"] == "🍓"


def test_hello(graphql_client):
    query = """query {
        hello
    }
    """

    result = graphql_client.query(query)

    assert result.data["hello"] == "🍓"


def test_hello_field(graphql_client):
    query = """query {
        helloField
    }
    """

    result = graphql_client.query(query)

    assert result.data["helloField"] == "I'm a function resolver"
