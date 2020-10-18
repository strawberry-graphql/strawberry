Release type: minor

Add support for adding a description to field arguments using the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) type:

```python
from typing import Annotated

@strawberry.type
class Query:
    @strawberry.field
    def user_by_id(id: Annotated[str, strawberry.argument(description="The ID of the user")]) -> User:
        ...
```

which results in the following schema:

```graphql
type Query {
  userById(
    """The ID of the user"""
    id: String
  ): User!
}
```

**Note:** if you are not using Python v3.9 or greater you will need to import `Annotated` from `typing_extensions`
