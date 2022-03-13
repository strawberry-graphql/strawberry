---
title: FAQ
faq: true
---

# Frequently Asked Questions

## How can I hide a field from GraphQL?

Strawberry provides a `Private` type that can be used to hide fields from
GraphQL, for example, the following code:

```python
import strawberry

@strawberry.type
class User:
    name: str
    age: int
    password: strawberry.Private[str]

@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100, password="This is fake")

schema = strawberry.Schema(query=Query)
```

will result in the following schema:

```graphql
type Query {
  user: User!
}

type User {
  name: String!
  age: Int!
}
```
