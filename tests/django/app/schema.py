import typing

import strawberry
from strawberry.apollo.schema_directives import CacheControl
from strawberry.extensions import ApolloCacheControlExtension, Extension
from strawberry.file_uploads import Upload


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Book:
    title: str
    cachedTitle: str = strawberry.field(directives=[CacheControl(max_age=30)])


@strawberry.type
class Reader:
    book: Book = strawberry.field(directives=[CacheControl(inheredit_max_age=True)])


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

    @strawberry.field
    def book(self) -> Book:
        return Book(
            title="The Boy, the Mole, the Fox and the Horse",
            cachedTitle="The Boy, the Mole, the Fox and the Horse",
        )

    @strawberry.field(directives=[CacheControl(max_age=60)])
    def cached_book(self) -> Book:
        return Book(title="Kill the Next One", cachedTitle="Kill the Next One")

    @strawberry.field(directives=[CacheControl(max_age=40)])
    def reader(self) -> Reader:
        return Reader(book=Book(title="The Help", cachedTitle="The Help"))


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[MyExtension, ApolloCacheControlExtension],
)
