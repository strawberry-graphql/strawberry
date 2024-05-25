Release type: minor

This release improves type checking for async resolver functions when used as
`strawberry.field(resolver=resolver_func)`.

Now doing this will raise a type error:

```python
import strawberry


def some_resolver() -> int:
    return 0


@strawberry.type
class User:
    # Note the field being typed as str instead of int
    name: str = strawberry.field(resolver=some_resolver)
```
