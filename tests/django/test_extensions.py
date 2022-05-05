def test_extensions(graphql_client):
    query = "{ hello }"

    response = graphql_client.query(query)

    assert response.extensions["example"] == "example"
