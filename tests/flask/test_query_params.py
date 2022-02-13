import json

from werkzeug.urls import url_encode, url_unparse


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

    query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
    response = flask_client_no_graphiql.get(query_url)

    assert response.status_code == 400


def test_no_graphiql_get_with_query_params(flask_client_no_graphiql):
    params = {
        "query": """
            query {
                hello
            }
        """
    }

    query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
    response = flask_client_no_graphiql.get(query_url)
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

    query_url = url_unparse(("", "", "/graphql", url_encode(params), ""))
    response = flask_client.post(query_url)

    assert response.status_code == 415
