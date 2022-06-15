import typing

import strawberry
from strawberry.extensions import Extension
from strawberry.file_uploads import Upload


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def hello(self) -> str:
        return "strawberry"

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

    @strawberry.mutation
    def match_text(self, text_file: Upload, pattern: str) -> str:
        text = text_file.read().decode()
        return pattern if pattern in text else ""


@strawberry.type
class Query:
    hello: str = "🍓"

    @strawberry.field
    def hi(self, name: str) -> str:
        return f"Hi {name}!"


schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[MyExtension])
