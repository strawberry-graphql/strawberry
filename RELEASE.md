Release type: patch

Allow using a static method as a resolver when the `self` argument is not
needed.

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    def static_text() -> str:
        return "Strawberry"
```
