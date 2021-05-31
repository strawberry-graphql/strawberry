Release type: minor

This release extends the file upload support of all integrations to support the upload
of file lists.

Here is an example how this would work with the ASGI integration.

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
        contents = []
        for file in files:
            content = (await file.read()).decode()
            contents.append(content)
        return contents
```

Check out the documentation to learn how the same can be done with other integrations.
