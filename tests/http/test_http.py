import pytest

from .clients import HttpClient


@pytest.mark.parametrize("method", ["delete", "head", "put", "patch"])
async def test_does_only_allow_get_and_post(
    method: str,
    http_client: HttpClient,
):
    response = await http_client.request(url="/graphql", method=method)  # type: ignore

    assert response.status_code == 405
