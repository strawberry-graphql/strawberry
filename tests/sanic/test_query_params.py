def test_no_graphiql_empty_get(sanic_client_no_graphiql):

    request, response = sanic_client_no_graphiql.test_client.get("/graphql")
    assert response.status == 404


def test_no_query(sanic_client):
    params = {"variables": '{"name": "James"}'}

    request, response = sanic_client.test_client.get("/graphql", params=params)
    assert response.status == 400


def test_get_with_query_params(sanic_client):
    params = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.get("/graphql", params=params)
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "Hello world"


def test_can_pass_variables_with_query_params(sanic_client):
    params = {
        "query": "query Hello($name: String!) { hello(name: $name) }",
        "variables": '{"name": "James"}',
    }

    request, response = sanic_client.test_client.get("/graphql", params=params)
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "Hello James"


def test_post_fails_with_query_params(sanic_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.post("/graphql", params=query)

    assert response.status == 415


def test_does_not_allow_mutation(sanic_client):
    query = {
        "query": """
            mutation {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.get("/graphql", params=query)

    assert response.status == 400
    assert "mutations are not allowed when using GET" in response.text


def test_fails_if_allow_queries_via_get_false(sanic_client_no_get):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client_no_get.test_client.get("/graphql", params=query)

    assert response.status == 400
    assert "queries are not allowed when using GET" in response.text
