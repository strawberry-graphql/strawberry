from django.core.files.uploadedfile import SimpleUploadedFile


def test_upload(graphql_client):
    f = SimpleUploadedFile("file.txt", b"strawberry")
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    response = graphql_client.query(
        query=query, variables={"textFile": None}, format="multipart", textFile=f
    )

    assert response.data["readText"] == "strawberry"


def test_file_list_upload(graphql_client):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

    response = graphql_client.query(
        query=query,
        variables={"files": [None, None]},
        format="multipart",
        file1=file1,
        file2=file2,
    )

    assert len(response.data["readFiles"]) == 2
    assert response.data["readFiles"][0] == "strawberry1"
    assert response.data["readFiles"][1] == "strawberry2"


def test_nested_file_list(graphql_client):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

    response = graphql_client.query(
        query=query,
        variables={"folder": {"files": [None, None]}},
        format="multipart",
        file1=file1,
        file2=file2,
    )

    assert len(response.data["readFolder"]) == 2
    assert response.data["readFolder"][0] == "strawberry1"
    assert response.data["readFolder"][1] == "strawberry2"
