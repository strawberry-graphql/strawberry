Release type: minor

Adds a `graphql_type` parameter to `strawberry.argument` that allows you
to explicitly override the GraphQL type of an argument, useful for static typing
when the Python type differs from the desired GraphQL type.

For example:

```python
BigInt = strawberry.scalar(
    int, name="BigInt", serialize=lambda v: str(v), parse_value=lambda v: int(v)
)


@strawberry.type
class Query:
    @strawberry.field()
    def username(
        self, user_id: Annotated[int, strawberry.argument(graphql_type=BigInt)]
    ) -> str:
        return "foobar"


schema = strawberry.Schema(Query)

str(
    schema
) == """
scalar BigInt

type Query {
  username(userId: BigInt!): String!
}
"""
```
