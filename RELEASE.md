release type: patch

This release fixes support for generic types so that now we can also use generics for input types:

```python
T = typing.TypeVar("T")

@strawberry.input
class Input(typing.Generic[T]):
    field: T

@strawberry.type
class Query:
    @strawberry.field
    def field(self, input: Input[str]) -> str:
        return input.field
```
