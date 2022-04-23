from typing import List, Optional

import strawberry
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: List[Upload]


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def hello(self) -> str:
        return "strawberry"

    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()

    @strawberry.mutation
    def read_files(self, files: List[Upload]) -> List[str]:
        return [file.read().decode() for file in files]

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> List[str]:
        return [file.read().decode() for file in folder.files]


schema = strawberry.Schema(query=Query, mutation=Mutation)
