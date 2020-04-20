import pytest

from starlette import status


@pytest.mark.parametrize("path", ("/", "/graphql"))
def test_renders_graphiql(path, schema, test_client):
    response = test_client.get(path)

    assert response.status_code == status.HTTP_200_OK

    assert "<title>Strawberry GraphiQL</title>" in response.text


@pytest.mark.parametrize("path", ("/", "/graphql"))
def test_renders_graphiql_disabled(path, schema, test_client_no_graphiql):
    response = test_client_no_graphiql.get(path)

    assert response.status_code == status.HTTP_404_NOT_FOUND
