import pytest

from fastapi import status


def test_returns_error_when_missing_query(test_client):
    response = test_client.post("/graphql", json={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_returns_error_when_not_sending_wrong_content_type(test_client):
    response = test_client.post("/graphql", data="Example")

    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE


@pytest.mark.parametrize("method", ("PUT", "DELETE"))
def test_returns_error_when_method_is_not_allowed(method, test_client):
    response = test_client.request(method, "/graphql", json={})

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
