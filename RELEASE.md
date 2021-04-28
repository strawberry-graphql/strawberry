Release type: patch

This release fixes an issue when using nested lists, this now works properly:

```python
def get_polygons() -> List[List[float]]:
    return [[2.0, 6.0]]

@strawberry.type
class Query:
    polygons: List[List[float]] = strawberry.field(resolver=get_polygons)

schema = strawberry.Schema(query=Query)

query = "{ polygons }"

result = schema.execute_sync(query, root_value=Query())
```
