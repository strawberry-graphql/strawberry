import json
import typing

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Query:
    hello: str = "strawberry"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()

    @strawberry.mutation
    def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            contents.append(file.read().decode())
        return contents

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> typing.List[str]:
        contents = []
        for file in folder.files:
            contents.append(file.read().decode())
        return contents


schema = strawberry.Schema(query=Query, mutation=Mutation)


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


def test_upload():
    f = SimpleUploadedFile("file.txt", b"strawberry")

    query = """mutation($textFile: Upload!) {
        readText(textFile: $textFile)
    }"""

    factory = RequestFactory()

    request = factory.post(
        "/graphql/",
        data={
            "operations": json.dumps({"query": query, "variables": {"textFile": None}}),
            "map": json.dumps({"textFile": ["variables.textFile"]}),
            "textFile": f,
        },
        format="multipart",
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert data["data"]["readText"] == "strawberry"


def test_file_list_upload():
    query = "mutation($files: [Upload!]!) { readFiles(files: $files) }"
    operations = json.dumps({"query": query, "variables": {"files": [None, None]}})
    file_map = json.dumps(
        {"file1": ["variables.files.0"], "file2": ["variables.files.1"]}
    )

    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

    factory = RequestFactory()
    request = factory.post(
        "/graphql/",
        data={
            "operations": operations,
            "map": file_map,
            "file1": file1,
            "file2": file2,
        },
        format="multipart",
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert len(data["data"]["readFiles"]) == 2
    assert data["data"]["readFiles"][0] == "strawberry1"
    assert data["data"]["readFiles"][1] == "strawberry2"


def test_nested_file_list():
    query = "mutation($folder: FolderInput!) { readFolder(folder: $folder) }"
    operations = json.dumps(
        {"query": query, "variables": {"folder": {"files": [None, None]}}}
    )
    file_map = json.dumps(
        {"file1": ["variables.folder.files.0"], "file2": ["variables.folder.files.1"]}
    )

    file1 = SimpleUploadedFile("file1.txt", b"strawberry1")
    file2 = SimpleUploadedFile("file2.txt", b"strawberry2")

    factory = RequestFactory()
    request = factory.post(
        "/graphql/",
        data={
            "operations": operations,
            "map": file_map,
            "file1": file1,
            "file2": file2,
        },
        format="multipart",
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert len(data["data"]["readFolder"]) == 2
    assert data["data"]["readFolder"][0] == "strawberry1"
    assert data["data"]["readFolder"][1] == "strawberry2"
