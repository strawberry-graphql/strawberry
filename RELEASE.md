Release type: minor

This release adds file upload support to the [Sanic](https://sanicframework.org)
integration. No additional configuration is required to enable file upload support.

The following example shows how a file upload based mutation could look like:

```python
import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class Mutation:
    @strawberry.mutation
    def read_text(self, text_file: Upload) -> str:
        return text_file.read().decode()
```
