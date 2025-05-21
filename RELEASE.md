release type: patch

This release fixes a long standing typing issue where mypy would
return the following error:

```text
main:14: error: Untyped decorator makes function "e" untyped  [misc] (diff)
```

When using the following code:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field(description="Get the last user")
    def last_user_v2(self) -> str:
        return "Hello"
```
