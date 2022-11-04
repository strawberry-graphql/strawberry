Release type: minor

This release changes the type resolution priority to prefer the field annotation over the resolver return type.

```python
def my_resolver() -> str:
    return "1.33"

@strawberry.type
class Query:
    a: float = strawberry.field(resolver=my_resolver)

schema = strawberry.Schema(Query)

# Before:
str(schema) == """
type Query {
  a: String!
}
"""

# After:
str(schema) == """
type Query {
  a: Float!
}
"""
```
