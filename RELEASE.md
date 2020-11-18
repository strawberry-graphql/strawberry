Release type: patch

Fix issue preventing reusing the same resolver for multiple fields, like here:

```python
def get_name(self) -> str:
    return "Name"

@strawberry.type
class Query:
    name: str = strawberry.field(resolver=get_name)
    name_2: str = strawberry.field(resolver=get_name)
```
