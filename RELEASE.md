Release type: minor

This release add the ability to disable query validation by setting
`validate_queries` to `False`

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello"


schema = strawberry.Schema(Query, validate_queries=validate_queries)
```
