Release type: patch

This release add query string into the info object that is sent to the resolver

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def query_string(self, info: Info) -> str:
        return info.query
```
