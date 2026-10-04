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

This doesn't work for an interface, or for a type that implements one, as inputs
can't implement interfaces: an input that subclasses them throws an
`InvalidSuperclassInterfaceError`. Move the fields to share to an undecorated
base model instead, and extend it from both the output type and the input:

```python
import pydantic
import strawberry


@strawberry.pydantic.interface
class Node(pydantic.BaseModel):
    id: strawberry.ID


class UserBase(pydantic.BaseModel):
    name: str
    email: str


@strawberry.pydantic.type
class User(UserBase, Node):
    pass


@strawberry.pydantic.input
class UserInput(UserBase):
    pass
```

The base model only shares the fields it declares. When the type extends another
decorated model, like `Admin(User)`, move the fields of that model to a base
model too, and extend it from the new base, like `class AdminBase(UserBase)`.
