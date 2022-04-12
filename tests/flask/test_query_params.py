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
