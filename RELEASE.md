Release type: patch

This release properly allows passing one argument to the `Info` class.

This is now fully supported:

```python
import strawberry

from typing import TypedDict


class Context(TypedDict):
    user_id: str


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info[Context]) -> str:
        return info.context["user_id"]
```
