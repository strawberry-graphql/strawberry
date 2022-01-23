def test_no_graphiql_empty_get(sanic_client_no_graphiql):

    request, response = sanic_client_no_graphiql.test_client.get("/graphql")
    assert response.status == 404


def test_no_graphiql_no_query(sanic_client_no_graphiql):
    params = {
        "variables": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client_no_graphiql.test_client.post(
        "/graphql", params=params
    )
    assert response.status == 400


def test_no_graphiql_get_with_query_params(sanic_client_no_graphiql):
    params = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client_no_graphiql.test_client.post(
        "/graphql", params=params
    )
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "strawberry"


def test_post_with_query_params(sanic_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.post("/graphql", params=query)
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "strawberry"
