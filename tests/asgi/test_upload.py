import json
import typing
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

    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode()
            contents.append(content)
        return contents


@pytest.fixture
def schema():
    return strawberry.Schema(query=Query, mutation=Mutation)


def test_single_file_upload(schema, test_client):
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


def test_file_list_upload(schema, test_client):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    operations = json.dumps({"query": query, "variables": {"files": [None, None]}})
    file_map = json.dumps(
        {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}
    )

    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = test_client.post(
        "/graphql/",
        data={
            "operations": operations,
            "map": file_map,
        },
        files={"file1": file1, "file2": file2},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert not data.get("errors")
    assert len(data["data"]["readFiles"]) == 2
    assert data["data"]["readFiles"][0] == "strawberry1"
    assert data["data"]["readFiles"][1] == "strawberry2"
