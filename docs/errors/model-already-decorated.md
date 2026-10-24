---
title: Model Already Decorated Error
---

# Model Already Decorated Error

## Description

This error is thrown when a Pydantic model is decorated more than once with
`strawberry.pydantic.type`, for example the following code will throw this
error:

```python
import pydantic
import strawberry


class Address(pydantic.BaseModel):
    street: str
    city: str


strawberry.pydantic.type(Address)
strawberry.pydantic.type(Address, name="Location")
```

This happens because a model can only have one GraphQL definition, so the second
decorator would replace the first one.

## How to fix this error

You can fix this error by removing one of the decorators. To publish the same
model as two GraphQL types, decorate a subclass of it:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class Address(pydantic.BaseModel):
    street: str
    city: str


@strawberry.pydantic.type
class Location(Address):
    pass
```

The subclass has the same fields and validation as the model it extends.
