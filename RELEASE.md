Release type: minor

This release changes how we handle generic type vars, bringing
support to the new generic syntax in Python 3.12 (which will be out in October).

This now works:

```python
@strawberry.type
class Edge[T]:
    cursor: strawberry.ID
    node_field: T


@strawberry.type
class Query:
    @strawberry.field
    def example(self) -> Edge[int]:
        return Edge(cursor=strawberry.ID("1"), node_field=1)


schema = strawberry.Schema(query=Query)
```
