from starlette import status


def test_no_graphiql_no_query(test_client_no_graphiql):
    response = test_client_no_graphiql.get(
        "/graphql", params={"variables": "{ hello }"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_no_graphiql_get_with_query_params(test_client_no_graphiql):
    response = test_client_no_graphiql.get("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {"hello": "Hello world"}}


def test_post_fails_with_query_params(test_client):
    response = test_client.post("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


def test_fails_mutation_using_get(test_client):
    response = test_client.get("/graphql", params={"query": "mutation { hello }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
