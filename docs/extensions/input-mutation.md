---
title: Input Mutation Extension
summary: Automatically create Input types for mutations
tags: QoL
---

# `InputMutationExtension`

The pattern of defining a mutation that receives a single
[input type](../types/input-types.md) argument called `input` is a common
practice in GraphQL. It helps to keep the mutation signatures clean and makes it
easier to manage complex mutations with multiple arguments.

The `InputMutationExtension` is a Strawberry field extension that allows you to
define a mutation with multiple arguments without having to manually create an
input type for it. Instead, it generates an input type based on the arguments of
the mutation resolver.

## Usage example:

```python
import strawberry
from strawberry.field_extensions import InputMutationExtension


@strawberry.type
class User:
    username: str


@strawberry.type
class Query:
    hello: str


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    def register_user(
        self,
        username: str,
        password: str,
    ) -> User:
        user = User(username=username)
        # maybe persist the user in a database
        return user


schema = strawberry.Schema(query=Query, mutation=Mutation)
```

The Strawberry schema above and the usage of the `InputMutationExtension` will
result in the following GraphQL schema:

```graphql
type User {
  username: String!
}

input RegisterUserInput {
  username: String!
  password: String!
}

type Mutation {
  registerUser(input: RegisterUserInput!): User!
}

type Query {
  hello: String!
}
```

## API reference:

_No arguments_
