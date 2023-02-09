Release type: patch

This release updates the typing for the resolver argument in
`strawberry.field`i to support async resolvers.
This means that now you won't get any type
error from Pyright when using async resolver, like the following example:

```python
import strawberry


async def get_user_age() -> int:
    return 0


@strawberry.type
class User:
    name: str
    age: int = strawberry.field(resolver=get_user_age)
```
