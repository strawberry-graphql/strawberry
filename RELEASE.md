Release type: minor

This release adds support for printing default values for scalars like JSON.

For example the following:

```python
import strawberry
from strawberry.scalars import JSON


@strawberry.input
class MyInput:
    j: JSON = strawberry.field(default_factory=dict)
    j2: JSON = strawberry.field(default_factory=lambda: {"hello": "world"})
```

will print the following schema:

```graphql
input MyInput {
    j: JSON! = {}
    j2: JSON! = {hello: "world"}
}
```
