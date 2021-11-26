Release type: patch

Allow using staticmethods and classmethods as resolvers

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    def static_text() -> str:
        return "Strawberry"

    @strawberry.field
    @classmethod
    def class_name(cls) -> str:
        return cls.__name__
```
