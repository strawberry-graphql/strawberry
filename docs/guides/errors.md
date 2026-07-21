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

## Partial responses for failed resolvers

By default, GraphQL allows partial responses when a resolver fails. This means
that successfully resolved fields are still returned alongside errors. However,
this applies only when the erroneous field is defined as optional.

Consider the following example:

```python
from typing import Optional
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def successful_field(self) -> Optional[str]:
        return "This field works"

    @strawberry.field
    def error_field(self) -> Optional[str]:
        raise Exception("This field fails")


schema = strawberry.Schema(query=Query)
```

<CodeGrid>

```graphql
{
  successfulField
  errorField
}
```

```json
{
  "data": {
    "successfulField": "This field works",
    "errorField": null
  },
  "errors": [
    {
      "message": "This field fails",
      "locations": [{ "line": 3, "column": 3 }],
      "path": ["errorField"]
    }
  ]
}
```

</CodeGrid>

The response includes both successfully resolved data and error details,
demonstrating GraphQL's ability to return partial results.

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

### Mapping expected exceptions to union results

If your application or integration already raises a specific exception for an
expected failure, you can map that exception to one of the GraphQL error types
in the field's return union by passing `exception_handlers` to
`strawberry.Schema`.

```python
import strawberry
from strawberry.types import Info
from strawberry.types.field import StrawberryField


class UsernameAlreadyExists(Exception):
    def __init__(self, username: str):
        self.username = username


@strawberry.type
class RegisterUserSuccess:
    user: User


@strawberry.type
class UsernameAlreadyExistsError:
    username: str


class UsernameAlreadyExistsHandler(
    strawberry.ExceptionHandler[UsernameAlreadyExists, UsernameAlreadyExistsError]
):
    def handle(
        self,
        exception: UsernameAlreadyExists,
        *,
        field: StrawberryField,
        info: Info,
    ) -> UsernameAlreadyExistsError:
        return UsernameAlreadyExistsError(username=exception.username)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def register_user(
        self, username: str, password: str
    ) -> RegisterUserSuccess | UsernameAlreadyExistsError:
        # create_user may raise UsernameAlreadyExists
        user = create_user(username, password)
        return RegisterUserSuccess(user=user)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    exception_handlers=[UsernameAlreadyExistsHandler()],
)
```

Strawberry only converts exceptions when both of these are true:

- the exception is an instance of the handler's declared exception type
- the field return type is a union, or nullable union, containing the handler's
  declared error type

The two type parameters — the exception type the handler receives and the
GraphQL error type it returns — are the single source of truth: they drive the
matching at runtime, and type checkers use them to verify the signature of
`handle` against the declared types.

To map several Python exception classes to the same GraphQL error type,
parameterize the handler with their union, e.g.
`strawberry.ExceptionHandler[ErrorA | ErrorB, MyErrorType]`.

If you prefer explicit class attributes — or you are not using a type checker —
the same handler can declare its types with `exception_type` and `error_type`
attributes instead of type parameters:

```python
class UsernameAlreadyExistsHandler(strawberry.ExceptionHandler):
    exception_type = UsernameAlreadyExists
    error_type = UsernameAlreadyExistsError

    def handle(self, exception, *, field, info):
        return UsernameAlreadyExistsError(username=exception.username)
```

With this style `exception_type` accepts a single exception type or a tuple of
them, and the attributes also cover types that are only known at runtime. You
can mix the styles — for example parameterize the exception and supply a
runtime-only `error_type` as an attribute — but declaring both a type parameter
and a conflicting attribute for the same slot raises a `TypeError` at schema
creation. Note that type checkers will not verify the signature of `handle` when
you use attributes.

Handlers cover exceptions raised by the resolver, during argument conversion,
and by field extensions (for example a permission or validation extension
wrapping the field). Argument conversion runs before the field-extension chain,
so a conversion error is mapped directly and bypasses the field extensions —
matching how conversion errors have always been raised before permissions run.
Field extensions may catch or transform resolver exceptions before the handler
sees the final exception leaving the extension chain.

If multiple handlers match, Strawberry uses the first matching handler from the
`exception_handlers` list. Handlers do not apply to subscription fields or to
list fields such as `list[Success | UsernameAlreadyExistsError]`.

A handler can decline an individual exception by returning `None` (or an
awaitable resolving to `None`). Declining re-raises the original exception, so
it propagates as a normal GraphQL error as if no handler had matched. This lets
`handle` act as a per-instance filter — match a broad exception type, but only
convert the instances you recognize:

```python
class ValidationErrorHandler(
    strawberry.ExceptionHandler[ValidationProblem, ValidationError]
):
    def handle(
        self,
        exception: ValidationProblem,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ValidationError | None:
        if exception.is_user_facing:
            return ValidationError(message=str(exception))
        # Not one we want to expose — let it propagate as a normal error.
        return None
```

When the error type is generic, parameterize the handler with the concrete
instantiation that appears in the union (for example
`strawberry.ExceptionHandler[MyError, ValidationError[int]]`), rather than the
bare generic (`ValidationError`), so it matches the correct member of the union.

Converted exceptions are treated as expected GraphQL results. They are not added
to the response's top-level `errors` list and are not passed to
`Schema.process_errors`, so avoid using broad exception types such as
`Exception` unless every matching error is safe to expose as a typed result.

On a synchronously executed field, `handle` must return its result
synchronously. An `async` handler returns a coroutine, which fails the same way
an `async` resolver does on a sync field: `execute_sync` returns an
`ExecutionResult` whose `errors` contain a `GraphQLError` stating that execution
could not complete synchronously.

---

## Additional resources:

[A Guide to GraphQL Errors | productionreadygraphql.com](https://productionreadygraphql.com/2020-08-01-guide-to-graphql-errors/)

[200 OK! Error Handling in GraphQL | sachee.medium.com](https://sachee.medium.com/200-ok-error-handling-in-graphql-7ec869aec9bc)
