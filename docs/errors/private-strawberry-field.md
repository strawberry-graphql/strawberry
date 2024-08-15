---
title: Private Strawberry Field Error
---

# Private Strawberry Field Error

## Description

This error is thrown when using both `strawberry.Private[Type]` and
`strawberry.field` on the same field, for example the following code will throw
this error:

```python
import strawberry


@strawberry.type
class Query:
    name: str
    age: strawberry.Private[int] = strawberry.field(name="ageInYears")


schema = strawberry.Schema(query=Query)
```

This happens because a `strawberry.Private` field is not going to be exposed in
the GraphQL schema, so using `strawberry.field` on that field won't be useful,
since it is meant to be used to change information about a field that is exposed
in the GraphQL schema.

<Note>
  This makes sense, but now we don't have a way to do something like:
  strawberry.Private[list[str]] = strawberry.field(default_factory=list)
  (workaround is to use dataclasses.field, explained below)
</Note>

## How to fix this error

You can fix this error by either removing the `strawberry.Private` annotation or
by removing the `strawberry.field` usage. If you need to specify a default value
using `default_factory` you can use `dataclasses.field` instead of
`strawberry.field`. For example:

```python
import strawberry
import dataclasses


@strawberry.type
class Query:
    name: str
    tags: strawberry.Private[str] = dataclasses.field(default_factory=list)


schema = strawberry.Schema(query=Query)
```
