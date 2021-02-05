import json
from io import BytesIO

import pytest

from starlette import status

import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Query:
    hello: str = "strawberry"


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_text(self, text_file: Upload) -> str:
        return (await text_file.read()).decode()


@pytest.fixture
def schema():
    return strawberry.Schema(query=Query, mutation=Mutation)


def test_upload(schema, test_client):
    f = BytesIO(b"strawberry")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = test_client.post(
        "/graphql/",
        data={
            "operations": json.dumps({"query": query, "variables": {"textFile": None}}),
            "map": json.dumps({"textFile": ["variables.textFile"]}),
        },
        files={"textFile": f},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"
