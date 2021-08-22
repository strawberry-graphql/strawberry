import pytest


def test_renders_graphiql(schema, test_client):
    response = test_client.get("/graphql")

    assert response.status_code == 200

    assert "<title>Strawberry GraphiQL</title>" in response.text


def test_renders_graphiql_disabled(schema, test_client_no_graphiql):
    response = test_client_no_graphiql.get("/graphql")

    assert response.status_code == 404
