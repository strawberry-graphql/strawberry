from io import BytesIO

from .clients import HttpClient


async def test_upload(http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }
    """

    response = await http_client.query(
        query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.json == {"data": {"readText": "strawberry"}}


async def test_file_list_upload(http_client: HttpClient):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = await http_client.query(
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

    response = await http_client.query(
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

    response = await http_client.query(
        query=query,
        variables={"files": [None, None], "textFile": None},
        files={"file1": file1, "file2": file2, "textFile": file3},
    )

    data = response.json["data"]
    assert len(data["readFiles"]) == 2
    assert data["readFiles"][0] == "strawberry1"
    assert data["readFiles"][1] == "strawberry2"
    assert data["readText"] == "strawberry3"


async def test_upload_invalid_query(http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readT
    """

    response = await http_client.query(
        query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.status_code == 200
    assert response.json == {
        "data": None,
        "errors": [
            {
                "locations": [{"column": 5, "line": 4}],
                "message": "Syntax Error: Expected Name, found <EOF>.",
            }
        ],
    }


async def test_upload_missing_file(http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }
    """

    response = await http_client.query(
        query,
        variables={"textFile": None},
        # using the wrong name to simulate a missing file
        # this is to make it easier to run tests with our client
        files={"a": f},
    )

    assert response.status_code == 400
    assert "File(s) missing in form data" in response.text
