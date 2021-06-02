Release type: patch

This release fixes the upload of nested file lists. Among other use cases, having an
input type like shown below is now working properly.

```python
import typing
import strawberry
from strawberry.file_uploads import Upload


@strawberry.input
class FolderInput:
    files: typing.List[Upload]
```
