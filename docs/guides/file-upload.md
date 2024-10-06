---
title: File Upload
---

# File Upload

All Strawberry integrations support multipart uploads as described in the
[GraphQL multipart request specification](https://github.com/jaydenseric/graphql-multipart-request-spec).
This includes support for uploading single files as well as lists of files.

## Security

Note that multipart file upload support is disabled by default in all
integrations. Before enabling multipart file upload support, make sure you
address the
[security implications outlined in the specification](https://github.com/jaydenseric/graphql-multipart-request-spec/blob/master/readme.md#security).
Usually, this entails enabling CSRF protection in your server framework (e.g.,
the `CsrfViewMiddleware` middleware in Django).

To enable file upload support, pass `multipart_uploads_enabled=True` to your
integration's view class. Refer to the integration-specific documentation for
more details on how to do this.

## Upload Scalar

Uploads can be used in mutations via the `Upload` scalar. The type passed at
runtime depends on the integration:

| Integration                               | Type                                                                                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [AIOHTTP](/docs/integrations/aiohttp)     | [`io.BytesIO`](https://docs.python.org/3/library/io.html#io.BytesIO)                                                                                  |
| [ASGI](/docs/integrations/asgi)           | [`starlette.datastructures.UploadFile`](https://www.starlette.io/requests/#request-files)                                                             |
| [Channels](/docs/integrations/channels)   | [`django.core.files.uploadedfile.UploadedFile`](https://docs.djangoproject.com/en/dev/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile) |
| [Django](/docs/integrations/django)       | [`django.core.files.uploadedfile.UploadedFile`](https://docs.djangoproject.com/en/dev/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile) |
| [FastAPI](/docs/integrations/fastapi)     | [`fastapi.UploadFile`](https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile)                                          |
| [Flask](/docs/integrations/flask)         | [`werkzeug.datastructures.FileStorage`](https://werkzeug.palletsprojects.com/en/latest/datastructures/#werkzeug.datastructures.FileStorage)           |
| [Quart](/docs/integrations/quart)         | [`quart.datastructures.FileStorage`](https://github.com/pallets/quart/blob/main/src/quart/datastructures.py)                                          |
| [Sanic](/docs/integrations/sanic)         | [`sanic.request.File`](https://sanic.readthedocs.io/en/stable/sanic/api/core.html#sanic.request.File)                                                 |
| [Starlette](/docs/integrations/starlette) | [`starlette.datastructures.UploadFile`](https://www.starlette.io/requests/#request-files)                                                             |

In order to have the correct runtime type in resolver type annotations you can
set a scalar override based on the integrations above. For example with
Starlette:

```python
import strawberry
from starlette.datastructures import UploadFile
from strawberry.file_uploads import Upload

schema = strawberry.Schema(
  ...
  scalar_overrides={UploadFile: Upload}
)
```

## ASGI / FastAPI / Starlette

Since these integrations use asyncio for communication, the resolver _must_ be
async.

Additionally, these servers rely on the `python-multipart` package, which is not
included by Strawberry by default. It can be installed directly, or, for
convenience, it is included in extras: `strawberry[asgi]` (for ASGI/Starlette)
or `strawberry[fastapi]` (for FastAPI). For example:

- if using Pip, `pip install 'strawberry[fastapi]'`
- if using Poetry, `strawberry = { version = "...", extras = ["fastapi"] }` in
  `pyproject.toml`.

Example:

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_file(self, file: Upload) -> str:
        return (await file.read()).decode("utf-8")

    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode("utf-8")
            contents.append(content)
        return contents

    @strawberry.mutation
    async def read_folder(self, folder: FolderInput) -> typing.List[str]:
        contents = []
        for file in folder.files:
            content = (await file.read()).decode("utf-8")
            contents.append(content)
        return contents
```

## Sanic / Flask / Django / Channels / AIOHTTP

Example:

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: typing.List[Upload]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_file(self, file: Upload) -> str:
        return file.read().decode("utf-8")

    @strawberry.mutation
    def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = file.read().decode("utf-8")
            contents.append(content)
        return contents

    @strawberry.mutation
    def read_folder(self, folder: FolderInput) -> typing.List[str]:
        contents = []
        for file in folder.files:
            contents.append(file.read().decode("utf-8"))
        return contents
```

## Sending file upload requests

The tricky part is sending the HTTP request from the client because it must
follow the GraphQL multipart request specifications mentioned above.

The `multipart/form-data` POST request's data must include:

- `operations` key for GraphQL request with query and variables
- `map` key with mapping some multipart-data to exact GraphQL variable
- and other keys for multipart-data which contains binary data of files

Assuming you have your schema up and running, here there are some requests
examples:

### Sending one file

```shell
curl localhost:8000/graphql \
  -F operations='{ "query": "mutation($file: Upload!){ readFile(file: $file) }", "variables": { "file": null } }' \
  -F map='{ "file": ["variables.file"] }' \
  -F file=@a.txt
```

### Sending a list of files

```shell
curl localhost:8000/graphql \
  -F operations='{ "query": "mutation($files: [Upload!]!) { readFiles(files: $files) }", "variables": { "files": [null, null] } }' \
  -F map='{"file1": ["variables.files.0"], "file2": ["variables.files.1"]}' \
  -F file1=@b.txt \
  -F file2=@c.txt
```

### Sending nested files

```shell
curl localhost:8000/graphql \
  -F operations='{ "query": "mutation($folder: FolderInput!) { readFolder(folder: $folder) }", "variables": {"folder": {"files": [null, null]}} }' \
  -F map='{"file1": ["variables.folder.files.0"], "file2": ["variables.folder.files.1"]}' \
  -F file1=@b.txt \
  -F file2=@c.txt
```
