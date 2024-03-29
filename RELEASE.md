Release type: minor

This release adds support for Apollo Federation in the schema codegen. Now you
can convert a schema like this:

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.3",
        import: ["@key", "@shareable"])

type Query {
  me: User
}

type User @key(fields: "id") {
  id: ID!
  username: String! @shareable
}
```

to a Strawberry powered schema like this:

```python
import strawberry


@strawberry.type
class Query:
    me: User | None


@strawberry.federation.type(keys=["id"])
class User:
    id: strawberry.ID
    username: str = strawberry.federation.field(shareable=True)


schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

By running the following command:

```bash
strawberry schema-codegen example.graphql
```
