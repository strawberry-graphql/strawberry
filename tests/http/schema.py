from typing import List, Optional

from starlette.datastructures import UploadFile

import strawberry
from strawberry.file_uploads import Upload
from strawberry.permission import BasePermission
from strawberry.types import Info


def _read_file(text_file: Upload) -> str:
    # allow to keep this function synchronous, starlette's files have
    # async methods for reading
    if isinstance(text_file, UploadFile):
        text_file = text_file.file._file  # type: ignore

    content = text_file.read()

    return content.decode()


@strawberry.input
class FolderInput:
    files: List[Upload]


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source: object, info: Info, **kwargs) -> bool:
        return False


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self) -> Optional[str]:
        return "Hey"

    @strawberry.field
    def root_name(self) -> str:
        return type(self).__name__


@strawberry.type
class Mutation:
    @strawberry.mutation
    def hello(self) -> str:
        return "strawberry"

    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return _read_file(text_file)

    @strawberry.mutation
    def read_files(self, files: List[Upload]) -> List[str]:
        return [_read_file(file) for file in files]

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> List[str]:
        return [_read_file(file) for file in folder.files]


schema = strawberry.Schema(query=Query, mutation=Mutation)
