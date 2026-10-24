---
title: Upload Field Error
---

# Upload Field Error

## Description

This error is thrown when a field of a `strawberry.pydantic.input` is typed as
`Upload`, for example the following code will throw this error:

```python
import pydantic
import strawberry
from strawberry.file_uploads import Upload


@strawberry.pydantic.input
class CreatePostInput(pydantic.BaseModel):
    title: str
    image: Upload
```

This happens because uploaded files are the file objects of your integration
(for example Starlette's `UploadFile`), and Pydantic would try to validate them
as the type behind `Upload`, rejecting every request.

## How to fix this error

You can fix this error by annotating the field with the file type of your
integration, and using `Upload` as its GraphQL type:

```python
from typing import Annotated

import pydantic
import strawberry
from starlette.datastructures import UploadFile
from strawberry.file_uploads import Upload


@strawberry.pydantic.input
class CreatePostInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    title: str
    image: Annotated[UploadFile, strawberry.field(graphql_type=Upload)]
```
