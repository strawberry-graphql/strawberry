---
title: Model Already Decorated Error
---

# Model Already Decorated Error

## Description

This error is thrown when a Pydantic model is decorated by more than one
`strawberry.pydantic` decorator, for example the following code will throw this
error:

```python
import pydantic
import strawberry


class Address(pydantic.BaseModel):
    street: str
    city: str


strawberry.pydantic.type(Address)
strawberry.pydantic.input(Address)
```

This happens because a model can only have one GraphQL definition, so the second
decorator would replace the first one.

## How to fix this error

To use the same model as an output type and as an input, decorate a subclass of
it:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class Address(pydantic.BaseModel):
    street: str
    city: str


@strawberry.pydantic.input
class AddressInput(Address):
    pass
```

The subclass has the same fields and validation as the model it extends.
