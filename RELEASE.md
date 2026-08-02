Release type: minor

Add native support for `typing.TypedDict` GraphQL object and input types via
the existing `@strawberry.type` and `@strawberry.input` decorators.

TypedDicts can now be used to define GraphQL schemas backed directly by Python
dictionaries, including support for nested TypedDicts, `Required`,
`NotRequired`, `total=False`, and `typing.Annotated` metadata. TypedDicts can
also participate in Strawberry unions, with runtime resolution based on
TypedDict shape.

Example:

```python
from typing import TypedDict

import strawberry


@strawberry.type
class User(TypedDict):
    id: int
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> User:
        return {"id": 1, "name": "Alice"}
```
