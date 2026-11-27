from io import BytesIO
from typing import NamedTuple

import pytest

import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Query:
    hello: str = "world"


@strawberry.input
class FolderInput:
    file: Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_file(self, file: Upload) -> str:
        return type(file).__name__

    @strawberry.mutation
    def read_files(self, files: list[Upload]) -> list[str]:
        return [type(file).__name__ for file in files]

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> str:
        return type(folder.file).__name__

    @strawberry.mutation
    def read_optional_file(self, file: Upload | None = None) -> str:
        return type(file).__name__


schema = strawberry.Schema(query=Query, mutation=Mutation)


class SanicFile(NamedTuple):
    """Mirrors `sanic.request.File`, which is a named tuple rather than a file."""

    type: str
    body: bytes
    name: str


@pytest.mark.parametrize(
    "value",
    [
        "not a file",
        42,
        3.14,
        True,
        {"not": "a file"},
        ["not a file"],
    ],
)
def test_upload_rejects_non_file_variables(value):
    result = schema.execute_sync(
        "mutation($file: Upload!) { readFile(file: $file) }",
        variable_values={"file": value},
    )

    assert result.data is None
    assert result.errors is not None
    assert "Upload cannot represent a non-file value" in result.errors[0].message


def test_upload_rejects_non_file_literals():
    result = schema.execute_sync('mutation { readFile(file: "not a file") }')

    assert result.data is None
    assert result.errors is not None
    assert "Upload cannot represent a non-file value" in result.errors[0].message


def test_upload_rejects_non_file_inside_input_type():
    result = schema.execute_sync(
        "mutation($folder: FolderInput!) { readFolder(folder: $folder) }",
        variable_values={"folder": {"file": "not a file"}},
    )

    assert result.data is None
    assert result.errors is not None
    assert "Upload cannot represent a non-file value" in result.errors[0].message


def test_upload_rejects_non_file_inside_list():
    result = schema.execute_sync(
        "mutation($files: [Upload!]!) { readFiles(files: $files) }",
        variable_values={"files": [BytesIO(b"strawberry"), "not a file"]},
    )

    assert result.data is None
    assert result.errors is not None
    assert "Upload cannot represent a non-file value" in result.errors[0].message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (BytesIO(b"strawberry"), "BytesIO"),
        (b"strawberry", "bytes"),
        # Integrations hand over their own file objects, so anything that isn't
        # a value a JSON decoder could have produced has to be accepted.
        (SanicFile("text/plain", b"strawberry", "file.txt"), "SanicFile"),
    ],
)
def test_upload_accepts_file_objects(value, expected):
    result = schema.execute_sync(
        "mutation($file: Upload!) { readFile(file: $file) }",
        variable_values={"file": value},
    )

    assert result.errors is None
    assert result.data == {"readFile": expected}


def test_upload_still_accepts_null_when_nullable():
    result = schema.execute_sync(
        "mutation($file: Upload) { readOptionalFile(file: $file) }",
        variable_values={"file": None},
    )

    assert result.errors is None
    assert result.data == {"readOptionalFile": "NoneType"}
