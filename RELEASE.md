Release type: minor

This release improves our support for generic types, now using the same the same
generic multiple times with a list inside an interface or union is supported,
for example the following will work:

```python
import strawberry


@strawberry.type
class BlockRow[T]:
    items: list[T]


@strawberry.type
class Query:
    @strawberry.field
    def blocks(self) -> list[BlockRow[str] | BlockRow[int]]:
        return [
            BlockRow(items=["a", "b", "c"]),
            BlockRow(items=[1, 2, 3, 4]),
        ]


schema = strawberry.Schema(query=Query)
```
