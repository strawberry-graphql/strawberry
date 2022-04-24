from io import BytesIO
from typing import Type

import pytest

from .clients import HttpClient


@pytest.mark.asyncio
async def test_upload(http_client_class: Type[HttpClient]):
    http_client = http_client_class()

    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }
    """

    response = await http_client.post(
        query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.json == {"data": {"readText": "strawberry"}}
