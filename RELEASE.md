Release type: patch

This release fixes a bug that prevented from extending a generic type when
passing a type, like here:

```python
T = typing.TypeVar("T")

@strawberry.interface
class Node(typing.Generic[T]):
    id: strawberry.ID

    def _resolve(self) -> typing.Optional[T]:
        return None

@strawberry.type
class Book(Node[str]):
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> typing.List[Book]:
        return list()
```
