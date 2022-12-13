Release type: minor

This PR adds a new `graphql_type` parameter to strawberry.field that allows you
to explicitly set the field type. This parameter will take preference over the
resolver return type and the class field type.

For example:

```python
@strawberry.type
class Query:
    a: float = strawberry.field(graphql_type=str)
    b = strawberry.field(graphql_type=int)

    @strawberry.field(graphql_type=float)
    def c(self) -> str:
        return "3.4"

schema = strawberry.Schema(Query)

str(schema) == """
  type Query {
    a: String!
    b: Int!
    c: Float!
  }
"""
```
