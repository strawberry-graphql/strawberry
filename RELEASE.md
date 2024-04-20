Release type: minor

This release improves our support for generic types, now using the same the same
generic multiple times with a list inside an interface or union is supported,
for example the following will work:

```python
import strawberry


@strawberry.type
class BlockRowType[T]:
    items: list[T]


@strawberry.type
class Query:
    @strawberry.field
    def blocks(self) -> list[BlockRowType[str] | BlockRowType[int]]:
        return [
            BlockRowType(id=strawberry.ID("3"), items=["a", "b", "c"]),
            BlockRowType(id=strawberry.ID("1"), items=[1, 2, 3, 4]),
        ]


schema = strawberry.Schema(query=Query)
```
