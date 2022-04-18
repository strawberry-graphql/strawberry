from starlette import status


def test_no_query(test_client):
    response = test_client.get("/graphql", params={"variables": '{"name": "James"}'})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_with_query_params(test_client):
    response = test_client.get("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {"hello": "Hello world"}}


def test_can_pass_variables_with_query_params(test_client):
    response = test_client.get(
        "/graphql",
        params={
            "query": "query Hello($name: String!) { hello(name: $name) }",
            "variables": '{"name": "James"}',
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data": {"hello": "Hello James"}}


def test_post_fails_with_query_params(test_client):
    response = test_client.post("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


def test_fails_mutation_using_get(test_client):
    response = test_client.get("/graphql", params={"query": "mutation { hello }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.text == "mutations are not allowed when using GET"


def test_fails_query_using_params_when_disabled(test_client_no_get):
    response = test_client_no_get.get("/graphql", params={"query": "{ hello }"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.text == "queries are not allowed when using GET"
