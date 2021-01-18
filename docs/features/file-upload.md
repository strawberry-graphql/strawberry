---
title: File Upload
---

# File Upload

Strawberry supports multipart uploads as described here: https://github.com/jaydenseric/graphql-multipart-request-spec for ASGI and Django.

Uploads can be used in mutations via the `Upload` type.

## ASGI

Since ASGI uses asyncio for communication the resolver _must_ be async as well.

Example:

```python
from strawberry.file_uploads import Upload
...
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def read_text(self, text_file: Upload) -> str:
        file_contents = await text_file.read()
        # do something awesome
        return "a string"
```

## Django

Documentation coming soon
