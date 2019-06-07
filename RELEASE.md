Release type: minor

Added support for optional fields with default arguments in the GraphQL schema when default arguments are passed to the resolver.

Example:
 ```python
@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info, name: str = "world") -> str:
        return name
```

```graphql
type Query {
    hello(name: String = "world"): String
}
```