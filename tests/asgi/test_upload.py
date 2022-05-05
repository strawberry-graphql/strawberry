from io import BytesIO


def test_single_file_upload(graphql_client):
    f = BytesIO(b"strawberry")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = graphql_client.query(
        query=query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.data["readText"] == "strawberry"


def test_file_list_upload(graphql_client):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = graphql_client.query(
        query=query,
        variables={"files": [None, None]},
        files={"file1": file1, "file2": file2},
    )
    assert len(response.data["readFiles"]) == 2
    assert response.data["readFiles"][0] == "strawberry1"
    assert response.data["readFiles"][1] == "strawberry2"


def test_nested_file_list(graphql_client):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = graphql_client.query(
        query=query,
        variables={"folder": {"files": [None, None]}},
        files={"file1": file1, "file2": file2},
    )

    assert len(response.data["readFolder"]) == 2
    assert response.data["readFolder"][0] == "strawberry1"
    assert response.data["readFolder"][1] == "strawberry2"


def test_upload_single_and_list_file_together(graphql_client):
    query = """
        mutation($files: [Upload!]!, $textFile: Upload!) {
            readFiles(files: $files)
            readText(textFile: $textFile)
        }
    """
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")
    file3 = BytesIO(b"strawberry3")

    response = graphql_client.query(
        query=query,
        variables={"files": [None, None], "textFile": None},
        files={"file1": file1, "file2": file2, "textFile": file3},
    )

    assert len(response.data["readFiles"]) == 2
    assert response.data["readFiles"][0] == "strawberry1"
    assert response.data["readFiles"][1] == "strawberry2"
    assert response.data["readText"] == "strawberry3"
