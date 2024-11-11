---
title: Dealing with errors
---

# Dealing with errors

There are multiple different types of errors in GraphQL and each can be handled
differently.

In this guide we will outline the different types of errors that you will
encounter when building a GraphQL server.

**Note**: By default Strawberry will log all execution errors to a
`strawberry.execution` logger:
[/docs/types/schema#handling-execution-errors](../types/schema#handling-execution-errors).

## GraphQL validation errors

GraphQL is strongly typed and so Strawberry validates all queries before
executing them. If a query is invalid it isn’t executed and instead the response
contains an `errors` list:

<CodeGrid>

```graphql
{
  hi
}
```

```json
{
  "data": null,
  "errors": [
    {
      "message": "Cannot query field 'hi' on type 'Query'.",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": null
    }
  ]
}
```

</CodeGrid>

Each error has a message, line, column and path to help you identify what part
of the query caused the error.

The validation rules are part of the GraphQL specification and built into
Strawberry, so there’s not really a way to customize this behavior. You can
disable all validation by using the
[DisableValidation](../extensions/disable-validation) extension.

## GraphQL type errors

When a query is executed each field must resolve to the correct type. For
example non-null fields cannot return None.

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return None


schema = strawberry.Schema(query=Query)
```

<CodeGrid>

```graphql
{
  hello
}
```

```json
{
  "data": null,
  "errors": [
    {
      "message": "Cannot return null for non-nullable field Query.hello.",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": ["hello"]
    }
  ]
}
```

</CodeGrid>

Each error has a message, line, column and path to help you identify what part
of the query caused the error.

## Unhandled execution errors

Sometimes a resolver will throw an unexpected error due to a programming error
or an invalid assumption. When this happens Strawberry catches the error and
exposes it in the top level `errors` field in the response.

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user() -> User:
        raise Exception("Can't find user")


schema = strawberry.Schema(query=Query)
```

<CodeGrid>

```graphql
{
  user {
    name
  }
}
```

```json
{
  "data": null,
  "errors": [
    {
      "message": "Can't find user",
      "locations": [
        {
          "line": 2,
          "column": 2
        }
      ],
      "path": ["user"]
    }
  ]
}
```

</CodeGrid>

## Expected errors

If an error is expected then it is often best to express it in the schema. This
allows the client to deal with the error in a robust way.

This could be achieved by making the field optional when there is a possibility
that the data won’t exist:

```python
from typing import Optional
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self, id: str) -> Optional[User]:
        try:
            user = get_a_user_by_their_ID
            return user
        except UserDoesNotExist:
            return None
```

When the expected error is more complicated it’s a good pattern to instead
return a union of types that either represent an error or a success response.
This pattern is often adopted with mutations where it’s important to be able to
return more complicated error details to the client.

For example, say you have a `registerUser` mutation where you need to deal with
the possibility that a user tries to register with a username that already
exists. You might structure your mutation type like this:

```python
import strawberry

from typing import Annotated, Union


@strawberry.type
class RegisterUserSuccess:
    user: User


@strawberry.type
class UsernameAlreadyExistsError:
    username: str
    alternative_username: str


# Create a Union type to represent the 2 results from the mutation
Response = Annotated[
    Union[RegisterUserSuccess, UsernameAlreadyExistsError],
    strawberry.union("RegisterUserResponse"),
]


@strawberry.mutation
def register_user(username: str, password: str) -> Response:
    if username_already_exists(username):
        return UsernameAlreadyExistsError(
            username=username,
            alternative_username=generate_username_suggestion(username),
        )

    user = create_user(username, password)
    return RegisterUserSuccess(user=user)
```

Then your client can look at the `__typename` of the result to determine what to
do next:

```graphql
mutation RegisterUser($username: String!, $password: String!) {
  registerUser(username: $username, password: $password) {
    __typename
    ... on UsernameAlreadyExistsError {
      alternativeUsername
    }
    ... on RegisterUserSuccess {
      user {
        id
        username
      }
    }
  }
}
```

This approach allows you to express the possible error states in the schema and
so provide a robust interface for your client to account for all the potential
outcomes from a mutation.

---

## Additional resources:

[A Guide to GraphQL Errors | productionreadygraphql.com](https://productionreadygraphql.com/2020-08-01-guide-to-graphql-errors/)

[200 OK! Error Handling in GraphQL | sachee.medium.com](https://sachee.medium.com/200-ok-error-handling-in-graphql-7ec869aec9bc)
