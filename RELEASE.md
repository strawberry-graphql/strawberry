Release type: minor

Add `query` property to `Info` class, allowing resolvers to access the GraphQL query string being executed via `info.query`.

Example usage:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info, name: str) -> str:
        print(info.query)
        return f"Hello {name}"
```

When executing this query:

```graphql
query Hello($name: String!) {
    hello(name: $name)
}
```

`info.query` returns the full query string:

```
"query Hello($name: String!) {\n    hello(name: $name)\n}"
```
