Release type: minor

This release adds support for generating Strawberry types from SDL files. For example, given the following SDL file:

```graphql
type Query {
  user: User
}

type User {
  id: ID!
  name: String!
}
```

you can run

```bash
strawberry schema-codegen schema.graphql
```

to generate the following Python code:

```python
import strawberry


@strawberry.type
class Query:
    user: User | None


@strawberry.type
class User:
    id: strawberry.ID
    name: str


schema = strawberry.Schema(query=Query)
```
