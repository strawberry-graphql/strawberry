import json
from io import BytesIO


def test_upload(flask_client):
    f = (BytesIO(b"strawberry"), "textFile.txt")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = flask_client.post(
        "/graphql",
        data={
            "operations": json.dumps({"query": query, "variables": {"textFile": None}}),
            "map": json.dumps({"textFile": ["variables.textFile"]}),
            "textFile": f,
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = json.loads(response.data.decode())

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"


def test_file_list_upload(flask_client):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    operations = json.dumps({"query": query, "variables": {"files": [None, None]}})
    file_map = json.dumps(
        {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}
    )

    file1 = (BytesIO(b"strawberry1"), "file1.txt")
    file2 = (BytesIO(b"strawberry2"), "file2.txt")

    response = flask_client.post(
        "/graphql",
        data={
            "operations": operations,
            "map": file_map,
            "file1": file1,
            "file2": file2,
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = json.loads(response.data.decode())

    assert not data.get("errors")
    assert len(data["data"]["readFiles"]) == 2
    assert data["data"]["readFiles"][0] == "strawberry1"
    assert data["data"]["readFiles"][1] == "strawberry2"


def test_nested_file_list(flask_client):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    operations = json.dumps(
        {"query": query, "variables": {"folder": {"files": [None, None]}}}
    )
    file_map = json.dumps(
        {"file1": ["variables.folder.files.0"], "file2": ["variables.folder.files.1"]}
    )

    file1 = (BytesIO(b"strawberry1"), "file1.txt")
    file2 = (BytesIO(b"strawberry2"), "file2.txt")

    response = flask_client.post(
        "/graphql",
        data={
            "operations": operations,
            "map": file_map,
            "file1": file1,
            "file2": file2,
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = json.loads(response.data.decode())

    assert not data.get("errors")
    assert len(data["data"]["readFolder"]) == 2
    assert data["data"]["readFolder"][0] == "strawberry1"
    assert data["data"]["readFolder"][1] == "strawberry2"
