import pytest


def test_returns_error_when_missing_query(schema, test_client):
    response = test_client.post("/graphql", json={})

    assert response.status_code == 422


def test_returns_error_when_not_sending_wrong_content_type(schema, test_client):
    response = test_client.post("/graphql", data="Example")

    assert response.status_code == 422


@pytest.mark.parametrize("method", ("PUT", "DELETE"))
def test_returns_error_when_method_is_not_allowed(method, schema, test_client):
    response = test_client.request(method, "/graphql", json={})

    assert response.status_code == 405
