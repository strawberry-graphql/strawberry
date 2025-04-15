from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import pytest

import strawberry
from strawberry.file_uploads import Upload

if TYPE_CHECKING:
    from sanic import Sanic


@strawberry.type
class Query:
    @strawberry.field
    def index(self) -> str:
        return "Hello there"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def file_upload(self, file: Upload) -> str:
        return file.name


@pytest.fixture
def app():
    from sanic import Sanic
    from strawberry.sanic.views import GraphQLView

    sanic_app = Sanic("sanic_testing")

    sanic_app.add_route(
        GraphQLView.as_view(
            schema=strawberry.Schema(query=Query, mutation=Mutation),
            multipart_uploads_enabled=True,
        ),
        "/graphql",
    )

    return sanic_app


def test_file_cast(app: Sanic):
    """Tests that the list of files in a sanic Request gets correctly turned into a dictionary"""
    from sanic.request import File
    from strawberry.sanic import utils

    file_name = "test.txt"

    file_content = b"Hello, there!."
    in_memory_file = BytesIO(file_content)
    in_memory_file.name = file_name

    form_data = {
        "operations": '{ "query": "mutation($file: Upload!){ fileUpload(file: $file) }", "variables": { "file": null } }',
        "map": '{ "file": ["variables.file"] }',
    }

    files = {
        "file": in_memory_file,
    }

    request, _ = app.test_client.post("/graphql", data=form_data, files=files)

    files = utils.convert_request_to_files_dict(request)  # type: ignore
    file = files["file"]

    assert isinstance(file, File)
    assert file.name == file_name
    assert file.body == file_content


def test_endpoint(app: Sanic):
    """Tests that the graphql api correctly handles file upload and processing"""
    file_name = "test.txt"

    file_content = b"Hello, there!"
    in_memory_file = BytesIO(file_content)
    in_memory_file.name = file_name

    form_data = {
        "operations": '{ "query": "mutation($file: Upload!){ fileUpload(file: $file) }", "variables": { "file": null } }',
        "map": '{ "file": ["variables.file"] }',
    }

    files = {
        "file": in_memory_file,
    }

    _, response = app.test_client.post("/graphql", data=form_data, files=files)

    assert response.json["data"]["fileUpload"] == file_name  # type: ignore
