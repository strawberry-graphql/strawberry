---
title: File Upload
---

# File Upload

All Strawberry integrations support multipart uploads as described in the
[GraphQL multipart request specification](https://github.com/jaydenseric/graphql-multipart-request-spec).
This includes support for uploading single files as well as lists of files.

Uploads can be used in mutations via the `Upload` scalar.

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
