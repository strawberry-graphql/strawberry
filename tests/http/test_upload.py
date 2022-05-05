import json
from io import BytesIO
from typing import Type

import pytest

import aiohttp

from .clients import HttpClient
from .clients.aiohttp import AioHttpClient
from .clients.asgi import AsgiHttpClient
from .clients.async_django import AsyncDjangoHttpClient
from .clients.chalice import ChaliceHttpClient
from .clients.django import DjangoHttpClient
from .clients.fastapi import FastAPIHttpClient
from .clients.flask import FlaskHttpClient
from .clients.sanic import SanicHttpClient


# redefining the fixtures to mark chalice tests as failing
@pytest.fixture(
    params=[
        AioHttpClient,
        AsgiHttpClient,
        AsyncDjangoHttpClient,
        DjangoHttpClient,
        FastAPIHttpClient,
        FlaskHttpClient,
        SanicHttpClient,
        pytest.param(
            ChaliceHttpClient,
            marks=pytest.mark.xfail(reason="Chalice does not support uploads"),
        ),
    ]
)
def http_client_class(request) -> Type[HttpClient]:
    return request.param


@pytest.fixture()
def http_client(http_client_class) -> HttpClient:
    return http_client_class()


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


class FakeWriter:
    def __init__(self):
        self.buffer = BytesIO()

    async def write(self, data: bytes):
        self.buffer.write(data)

    @property
    def value(self) -> bytes:
        return self.buffer.getvalue()


async def test_extra_form_data_fields_are_ignored(http_client: HttpClient):
    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    f = BytesIO(b"strawberry")
    operations = json.dumps({"query": query, "variables": {"textFile": None}})
    file_map = json.dumps({"textFile": ["variables.textFile"]})
    extra_field_data = json.dumps({})

    form_data = aiohttp.FormData()
    form_data.add_field("textFile", f, filename="textFile.txt")
    form_data.add_field("operations", operations)
    form_data.add_field("map", file_map)
    form_data.add_field("extra_field", extra_field_data)

    buffer = FakeWriter()
    writer = form_data()

    await (writer.write(buffer))  # type: ignore

    response = await http_client.post(
        url="/graphql",
        data=buffer.value,
        headers={"content-type": writer.content_type},
    )

    assert response.status_code == 200
    assert response.json["data"] == {"readText": "strawberry"}


async def test_sending_invalid_form_data(http_client: HttpClient):
    headers = {"content-type": "multipart/form-data; boundary=----fake"}
    response = await http_client.post("/graphql", headers=headers)

    assert response.status_code == 400
    # TODO: can we consolidate this?
    # - aiohttp returns "Unable to parse the multipart body"
    # - fastapi returns "No valid query was provided for the request"
    assert (
        "Unable to parse the multipart body" in response.text
        or "No GraphQL query found in the request" in response.text
        or "No valid query was provided for the request" in response.text
    )


async def test_sending_invalid_json_body(http_client: HttpClient):
    f = BytesIO(b"strawberry")
    operations = "}"
    file_map = json.dumps({"textFile": ["variables.textFile"]})

    form_data = aiohttp.FormData()
    form_data.add_field("textFile", f, filename="textFile.txt")
    form_data.add_field("operations", operations)
    form_data.add_field("map", file_map)

    buffer = FakeWriter()
    writer = form_data()

    await (writer.write(buffer))  # type: ignore

    response = await http_client.post(
        "/graphql",
        data=buffer.value,
        headers={"content-type": writer.content_type},
    )

    assert response.status_code == 400
    assert (
        "Unable to parse the multipart body" in response.text
        or "Unable to parse request body as JSON" in response.text
    )
