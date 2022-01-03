---
title: File Upload
---

# File Upload

All Strawberry integrations support multipart uploads as described in the
[GraphQL multipart request specification](https://github.com/jaydenseric/graphql-multipart-request-spec).
This includes support for uploading single files as well as lists of files.

Uploads can be used in mutations via the `Upload` scalar.
The type passed at runtime depends on the integration:

| Integration                               | Type                                                                                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [AIOHTTP](/docs/integrations/aiohttp)     | [`io.BytesIO`](https://docs.python.org/3/library/io.html#io.BytesIO)                                                                                  |
| [ASGI](/docs/integrations/asgi)           | [`starlette.datastructures.UploadFile`](https://www.starlette.io/requests/#request-files)                                                             |
| [Django](/docs/integrations/django)       | [`django.core.files.uploadedfile.UploadedFile`](https://docs.djangoproject.com/en/3.2/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile) |
| [FastAPI](/docs/integrations/fastapi)     | [`fastapi.UploadFile`](https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile)                                          |
| [Flask](/docs/integrations/flask)         | [`werkzeug.datastructures.FileStorage`](https://werkzeug.palletsprojects.com/en/2.0.x/datastructures/#werkzeug.datastructures.FileStorage)            |
| [Sanic](/docs/integrations/sanic)         | [`sanic.request.File`](https://sanic.readthedocs.io/en/stable/sanic/api/core.html#sanic.request.File)                                                 |
| [Starlette](/docs/integrations/starlette) | [`starlette.datastructures.UploadFile`](https://www.starlette.io/requests/#request-files)                                                             |

## ASGI

Since ASGI uses asyncio for communication the resolver _must_ be async as well.

Example:

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_file(self, file: Upload) -> str:
        return await file.read()

    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode()
            contents.append(content)
        return contents
```

## Sanic / Flask / Django / AIOHTTP

Example:

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_file(self, file: Upload) -> str:
        return file.read().decode()

    @strawberry.mutation
    def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = file.read().decode()
            contents.append(content)
        return contents
```
