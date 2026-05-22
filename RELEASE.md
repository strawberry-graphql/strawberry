Release type: patch

Add native support for `typing.TypedDict` GraphQL object and input types via
the new `@strawberry.typed_dict` and `@strawberry.typed_dict_input` decorators.

TypedDicts can now be used to define GraphQL schemas backed directly by Python
dictionaries, including support for nested TypedDicts, `Required`,
`NotRequired`, `total=False`, and `typing.Annotated` metadata.

Example:

```python
from typing import TypedDict

import strawberry


@strawberry.typed_dict
class User(TypedDict):
    id: int
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> User:
        return {"id": 1, "name": "Alice"}
```
