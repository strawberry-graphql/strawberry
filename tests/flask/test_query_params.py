import json


def test_no_graphiql_empty_get(flask_client_no_graphiql):

    response = flask_client_no_graphiql.get("/graphql")

    assert response.status_code == 415


def test_no_graphiql_no_query(flask_client_no_graphiql):
    params = {
        "variables": """
            query {
                hello
            }
        """
    }

    response = flask_client_no_graphiql.get("/graphql", query_string=params)

    assert response.status_code == 400


def test_no_graphiql_get_with_query_params(flask_client_no_graphiql):
    params = {
        "query": """
            query {
                hello
            }
        """
    }

    response = flask_client_no_graphiql.get("/graphql", query_string=params)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "strawberry"


def test_no_graphiql_post_fails_with_query_params(flask_client):
    params = {
        "query": """
            query {
                hello
            }
        """
    }

    response = flask_client.post("/graphql", query_string=params)

    assert response.status_code == 415


def test_does_not_allow_mutation(flask_client):
    query = {
        "query": """
            mutation {
                hello
            }
        """
    }

    response = flask_client.get("/graphql", query_string=query)

    assert response.status_code == 400
    assert "mutations are not allowed when using GET" in response.text


def test_fails_if_allow_queries_via_get_false(flask_client_no_get):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = flask_client_no_get.get("/graphql", query_string=query)

    assert response.status_code == 400
    assert "queries are not allowed when using GET" in response.text
