Release type: patch

Bugfix to allow the use of `UNSET` as a default value for arguments.

```python
import strawberry
from strawberry.arguments import UNSET, is_unset

@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: Optional[str] = UNSET) -> str:
        if is_unset(name):
            return "Hi there"
        return "Hi {name}"

schema = strawberry.Schema(query=Query)

result = schema.execute_async("{ hello }")
assert result.data == {"hello": "Hi there"}

result = schema.execute_async('{ hello(name: "Patrick" }')
assert result.data == {"hello": "Hi Patrick"}
```

SDL:

```graphql
type Query {
  hello(name: String): String!
}
```
