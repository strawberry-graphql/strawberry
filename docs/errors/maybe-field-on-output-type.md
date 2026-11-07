---
title: Maybe Field On Output Type Error
---

# Maybe Field On Output Type Error

## Description

This error is thrown when a field of a type or an interface is typed as
`strawberry.Maybe`, for example the following code will throw this error:

```python
import strawberry


@strawberry.type
class User:
    name: strawberry.Maybe[str]
```

`Maybe` is for inputs: it tells the fields a client left out apart from the ones
it set to `null`. GraphQL has no value for an output field that was left out, so
the `strawberry.Some` holding the value would be serialized as its repr, like
`"Some('Ada')"`.

The error is raised when the schema is built, for fields and for resolvers
returning a `Maybe`, also inside a list or an optional, like
`list[strawberry.Maybe[str]]`, and for Pydantic models decorated with
`@strawberry.pydantic.type` or `@strawberry.pydantic.interface`.

## How to fix this error

Make the field nullable instead:

```python
import strawberry


@strawberry.type
class User:
    name: str | None
```

If the field was declared on a type to share it with an input, move it to the
input, or to a base input both inherit from:

```python
import strawberry


@strawberry.type
class User:
    name: str | None


@strawberry.input
class UpdateUserInput:
    name: strawberry.Maybe[str]
```
