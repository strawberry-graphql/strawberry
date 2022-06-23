Release type: patch

This release adds support in Mypy for using strawberry.mutation
while passing a resolver, the following now doesn't make Mypy return
an error:

```python
import strawberry

def set_name(self, name: str) -> None:
    self.name = name

@strawberry.type
class Mutation:
    set_name: None = strawberry.mutation(resolver=set_name)
```
