from django.core.files.uploadedfile import SimpleUploadedFile


def test_upload(graphql_client):
    f = SimpleUploadedFile("file.txt", b"strawberry")
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
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

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
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

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
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")
    file3 = SimpleUploadedFile("file3.txt", b"strawberry3")

    response = graphql_client.query(
        query=query,
        variables={"files": [None, None], "textFile": None},
        files={"file1": file1, "file2": file2, "textFile": file3},
    )

    assert len(response.data["readFiles"]) == 2
    assert response.data["readFiles"][0] == "strawberry1"
    assert response.data["readFiles"][1] == "strawberry2"
    assert response.data["readText"] == "strawberry3"


def test_mixed_files_and_variables(graphql_client):
    f = SimpleUploadedFile("file.txt", b"strawberry is great!")
    query = """mutation($textFile: Upload!, $pattern: String!) {
        matchText(textFile: $textFile, pattern: $pattern)
    }"""

    response = graphql_client.query(
        query=query,
        variables={"textFile": None, "pattern": "strawberry"},
        files={"textFile": f},
    )

    assert response.data["matchText"] == "strawberry"


def test_mixed_variables_and_list_file_together(graphql_client):
    query = """
        mutation(
            $files: [Upload!]!,
            $textFile: Upload!,
            $otherFile: Upload!,
            $pattern: String!
        ) {
            readFiles(files: $files)
            readText(textFile: $textFile)
            matchText(textFile: $otherFile, pattern: $pattern)
        }
    """
    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")
    file3 = SimpleUploadedFile("file3.txt", b"strawberry3")
    file4 = SimpleUploadedFile("file4.txt", b"4 strawberry 4")

    response = graphql_client.query(
        query=query,
        variables={
            "files": [None, None],
            "textFile": None,
            "otherFile": None,
            "pattern": "strawberry",
        },
        files={"file1": file1, "file2": file2, "textFile": file3, "otherFile": file4},
    )

    assert len(response.data["readFiles"]) == 2
    assert response.data["readFiles"][0] == "strawberry1"
    assert response.data["readFiles"][1] == "strawberry2"
    assert response.data["readText"] == "strawberry3"
    assert response.data["matchText"] == "strawberry"
