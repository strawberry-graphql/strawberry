import contextlib
import json
from io import BytesIO

import pytest
from urllib3 import encode_multipart_formdata

from .clients.base import HttpClient


@pytest.fixture
def http_client(http_client_class: type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        from .clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.xfail(reason="Chalice does not support uploads")

    return http_client_class()


@pytest.fixture
def enabled_http_client(http_client_class: type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        from .clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.xfail(reason="Chalice does not support uploads")

    return http_client_class(multipart_uploads_enabled=True)


async def test_multipart_uploads_are_disabled_by_default(http_client: HttpClient):
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

    assert response.status_code == 400
    assert response.data == b"Unsupported content type"


async def test_upload(enabled_http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }
    """

    response = await enabled_http_client.query(
        query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.json.get("errors") is None
    assert response.json["data"] == {"readText": "strawberry"}


async def test_file_list_upload(enabled_http_client: HttpClient):
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = await enabled_http_client.query(
        query=query,
        variables={"files": [None, None]},
        files={"file1": file1, "file2": file2},
    )

    data = response.json["data"]

    assert len(data["readFiles"]) == 2
    assert data["readFiles"][0] == "strawberry1"
    assert data["readFiles"][1] == "strawberry2"


async def test_nested_file_list(enabled_http_client: HttpClient):
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")

    response = await enabled_http_client.query(
        query=query,
        variables={"folder": {"files": [None, None]}},
        files={"file1": file1, "file2": file2},
    )

    data = response.json["data"]
    assert len(data["readFolder"]) == 2
    assert data["readFolder"][0] == "strawberry1"
    assert data["readFolder"][1] == "strawberry2"


async def test_upload_single_and_list_file_together(enabled_http_client: HttpClient):
    query = """
        mutation($files: [Upload!]!, $textFile: Upload!) {
            readFiles(files: $files)
            readText(textFile: $textFile)
        }
    """
    file1 = BytesIO(b"strawberry1")
    file2 = BytesIO(b"strawberry2")
    file3 = BytesIO(b"strawberry3")

    response = await enabled_http_client.query(
        query=query,
        variables={"files": [None, None], "textFile": None},
        files={"file1": file1, "file2": file2, "textFile": file3},
    )

    data = response.json["data"]
    assert len(data["readFiles"]) == 2
    assert data["readFiles"][0] == "strawberry1"
    assert data["readFiles"][1] == "strawberry2"
    assert data["readText"] == "strawberry3"


async def test_upload_invalid_query(enabled_http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readT
    """

    response = await enabled_http_client.query(
        query,
        variables={"textFile": None},
        files={"textFile": f},
    )

    assert response.status_code == 200
    assert response.json["data"] is None
    assert response.json["errors"] == [
        {
            "locations": [{"column": 5, "line": 4}],
            "message": "Syntax Error: Expected Name, found <EOF>.",
        }
    ]


async def test_upload_missing_file(enabled_http_client: HttpClient):
    f = BytesIO(b"strawberry")

    query = """
    mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }
    """

    response = await enabled_http_client.query(
        query,
        variables={"textFile": None},
        # using the wrong name to simulate a missing file
        # this is to make it easier to run tests with our client
        files={"a": f},
    )

    assert response.status_code == 400
    assert "File(s) missing in form data" in response.text


class FakeWriter:
    def __init__(self):
        self.buffer = BytesIO()

    async def write(self, data: bytes):
        self.buffer.write(data)

    @property
    def value(self) -> bytes:
        return self.buffer.getvalue()


async def test_extra_form_data_fields_are_ignored(enabled_http_client: HttpClient):
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    f = BytesIO(b"strawberry")
    operations = json.dumps({"query": query, "variables": {"textFile": None}})
    file_map = json.dumps({"textFile": ["variables.textFile"]})
    extra_field_data = json.dumps({})

    f = BytesIO(b"strawberry")
    fields = {
        "operations": operations,
        "map": file_map,
        "extra_field": extra_field_data,
        "textFile": ("textFile.txt", f.read(), "text/plain"),
    }

    data, header = encode_multipart_formdata(fields)

    response = await enabled_http_client.post(
        url="/graphql",
        data=data,
        headers={
            "content-type": header,
            "content-length": f"{len(data)}",
        },
    )

    assert response.status_code == 200
    assert response.json["data"] == {"readText": "strawberry"}


async def test_sending_invalid_form_data(enabled_http_client: HttpClient):
    headers = {"content-type": "multipart/form-data; boundary=----fake"}
    response = await enabled_http_client.post("/graphql", headers=headers)

    assert response.status_code == 400
    # TODO: consolidate this, it seems only AIOHTTP returns the second error
    # due to validating the boundary
    assert (
        "No GraphQL query found in the request" in response.text
        or "Unable to parse the multipart body" in response.text
    )


@pytest.mark.aiohttp
async def test_sending_invalid_json_body(enabled_http_client: HttpClient):
    f = BytesIO(b"strawberry")
    operations = "}"
    file_map = json.dumps({"textFile": ["variables.textFile"]})

    fields = {
        "operations": operations,
        "map": file_map,
        "textFile": ("textFile.txt", f.read(), "text/plain"),
    }

    data, header = encode_multipart_formdata(fields)

    response = await enabled_http_client.post(
        "/graphql",
        data=data,
        headers={
            "content-type": header,
            "content-length": f"{len(data)}",
        },
    )

    assert response.status_code == 400
    assert (
        "Unable to parse the multipart body" in response.text
        or "Unable to parse request body as JSON" in response.text
    )
