---
title: Object is not an Enum Error
---

# Object is not an Enum Error

## Description

This error is thrown when applying `@strawberry.enum` to a non-enum object, for
example the following code will throw this error:

```python
import strawberry


# note the lack of @strawberry.enum here:
class NotAnEnum:
    A = "A"


@strawberry.type
class Query:
    field: NotAnEnum


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry expects all enums to be subclasses of `Enum`.

## How to fix this error

You can fix this error by making sure the class you're applying
`@strawberry.enum` to is a subclass of `Enum`. For example, the following code
will fix this error:

```python
import strawberry


@strawberry.enum
class NotAnEnum:
    A = "A"


@strawberry.type
class Query:
    field: NotAnEnum


schema = strawberry.Schema(query=Query)
```
