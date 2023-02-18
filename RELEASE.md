release type: minor

Adds support for a custom field using the approach specified in issue [#2168](abc).
Field Extensions may be used to change the way how fields work and what they return.
Use cases might include pagination, permissions or other behavior modifications.

```python
from strawberry.extensions import FieldExtension


class UpperCaseExtension(FieldExtension):
    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ):
        result = await next(source, info, **kwargs)
        return str(result).upper()


@strawberry.type
class Query:
    @strawberry.field(extensions=[UpperCaseExtension()])
    async def string(self) -> str:
        return "This is a test!!"
```

```gql
query {
    string
}
```

```json
{
  "string": "THIS IS A TEST!!"
}
```
