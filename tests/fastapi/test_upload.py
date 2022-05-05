import json
from io import BytesIO

from fastapi import status


def test_single_file_upload(test_client):
    f = BytesIO(b"strawberry")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = test_client.post(
        "/graphql",
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


def test_file_list_upload(test_client):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    operations = json.dumps({"query": query, "variables": {"files": [None, None]}})
    file_map = json.dumps(
        {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}
    )

    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = test_client.post(
        "/graphql",
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


def test_nested_file_list(test_client):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    operations = json.dumps(
        {"query": query, "variables": {"folder": {"files": [None, None]}}}
    )
    file_map = json.dumps(
        {"file1": ["variables.folder.files.0"], "file2": ["variables.folder.files.1"]}
    )

    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = test_client.post(
        "/graphql",
        data={
            "operations": operations,
            "map": file_map,
        },
        files={"file1": file1, "file2": file2},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert not data.get("errors")
    assert len(data["data"]["readFolder"]) == 2
    assert data["data"]["readFolder"][0] == "strawberry1"
    assert data["data"]["readFolder"][1] == "strawberry2"
