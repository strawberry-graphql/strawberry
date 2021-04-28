---
title: Tools
---

# Tools

Strawberry provides some utility functions to help you build your GraphQL
server. All tools can be imported from `strawberry.tools`

---

### `create_type`

Creates a Strawberry type from a list of StrawberryFields.

```python
def create_type(name: str, fields: List[StrawberryField]) -> Type:
    ...
```

Example:

```python+schema
import strawberry
from strawberry.tools import create_type

@strawberry.field
def get_user_by_username(username: str) -> User:
    user = ...  # get user
    return User(username=user.username)

@strawberry.mutation
def create_user(username: str) -> User:
    user = ...  # create user
    return User(username=user.username)

Query = create_type("Query", [get_user_by_username])

Mutation = create_type("Mutation", [create_user])

schema = strawberry.Schema(query=Query, mutation=Mutation)
---
type Mutation {
  createUser(username: String!): User!
}

type Query {
  getUserByUsername(username: String!): User!
}

type User {
  username: String!
}
```
