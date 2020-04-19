import pytest

from starlette import status


@pytest.mark.parametrize("path", ("/", "/graphql"))
def test_renders_graphiql(path, schema, test_client):
    response = test_client.get(path)

    assert response.status_code == status.HTTP_200_OK

    assert "<title>Strawberry GraphiQL</title>" in response.text
    assert f"var fetchURL = 'http://testserver{path}';" in response.text
