---
title: Resolver Not A Function Error
---

# Resolver Not A Function Error

## Description

This error is thrown when `strawberry.pydantic.field` is given a resolver that
isn't a function, like a bound method, a built-in function or a callable object.
For example the following code will throw this error:

```python
import pydantic
import strawberry


class Formatter:
    def label(self, root: "Ticket") -> str:
        return f"#{root.id}"


formatter = Formatter()


@strawberry.pydantic.type
class Ticket(pydantic.BaseModel):
    id: int

    label = strawberry.pydantic.field(formatter.label)
```

This happens because `strawberry.pydantic.field` returns the resolver, which
stays in the model's class body, and Pydantic only allows fields and functions
there (including methods, static methods and class methods). Functions defined
outside of the model, and `functools.partial` objects, can be used.

## How to fix this error

You can fix this error by adding a method to the model that calls the resolver:

```python
import pydantic
import strawberry


class Formatter:
    def label(self, root: "Ticket") -> str:
        return f"#{root.id}"


formatter = Formatter()


@strawberry.pydantic.type
class Ticket(pydantic.BaseModel):
    id: int

    @strawberry.pydantic.field
    def label(self) -> str:
        return formatter.label(self)
```
