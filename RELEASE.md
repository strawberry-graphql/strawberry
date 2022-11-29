Release type: patch

 Generic types are now allowed in the schema's extra types.
```python
T = TypeVar('T')

@strawberry.type
class Node(Generic[T]):
    field: T

@strawberry.type
class Query:
    name: str

schema = strawberry.Schema(Query, types=[Node[int]])
```
