from io import BytesIO

import pytest

from .clients import HttpClient


@pytest.mark.asyncio
async def test_upload(http_client: HttpClient):
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


async def test_file_list_upload(http_client: HttpClient):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = await http_client.post(
        query=query,
        variables={"files": [None, None]},
        files={"file1": file1, "file2": file2},
    )

    data = response.json["data"]

    assert len(data["readFiles"]) == 2
    assert data["readFiles"][0] == "strawberry1"
    assert data["readFiles"][1] == "strawberry2"


async def test_nested_file_list(http_client: HttpClient):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = await http_client.post(
        query=query,
        variables={"folder": {"files": [None, None]}},
        files={"file1": file1, "file2": file2},
    )

    data = response.json["data"]
    assert len(data["readFolder"]) == 2
    assert data["readFolder"][0] == "strawberry1"
    assert data["readFolder"][1] == "strawberry2"


async def test_upload_single_and_list_file_together(http_client: HttpClient):
    query = """
        mutation($files: [Upload!]!, $textFile: Upload!) {
            readFiles(files: $files)
            readText(textFile: $textFile)
        }
    """
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")
    file3 = BytesIO(b"strawberry3")

    response = await http_client.post(
        query=query,
        variables={"files": [None, None], "textFile": None},
        files={"file1": file1, "file2": file2, "textFile": file3},
    )

    data = response.json["data"]
    assert len(data["readFiles"]) == 2
    assert data["readFiles"][0] == "strawberry1"
    assert data["readFiles"][1] == "strawberry2"
    assert data["readText"] == "strawberry3"
