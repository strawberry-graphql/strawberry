Release type: patch

This release adds `UploadDefinition` to `strawberry.file_uploads`, which can be
used with `scalar_overrides` to map framework-specific upload types to the
`Upload` scalar. This enables proper type checking with mypy/pyright when using
file uploads.

Example usage with Starlette/FastAPI:

```python
from starlette.datastructures import UploadFile
from strawberry.file_uploads import UploadDefinition

schema = strawberry.Schema(
    query=Query, mutation=Mutation, scalar_overrides={UploadFile: UploadDefinition}
)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_file(self, file: UploadFile) -> str:
        return (await file.read()).decode("utf-8")
```

With this configuration, the `file` parameter is correctly typed as `UploadFile`,
giving you proper IDE autocomplete and type checking.
