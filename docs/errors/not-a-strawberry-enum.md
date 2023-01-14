---
title: Not a Strawberry Enum Error
---

# Not a Strawberry Enum Error

## Description

This error is thrown when trying to use an enum that is not a Strawberry enum,
for example the following code will throw this error:

```python
import strawberry


# note the lack of @strawberry.enum here:
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value(
        "strawberry",
        description="Our favourite",
    )
    CHOCOLATE = "chocolate"


@strawberry.type
class Query:
    field: IceCreamFlavour


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry expects all enums to be decorated with
`@strawberry.enum`.

## How to fix this error

You can fix this error by making sure the enum you're using is decorated with
`@strawberry.enum`. For example, the following code will fix this error:

```python
import strawberry


@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value(
        "strawberry",
        description="Our favourite",
    )
    CHOCOLATE = "chocolate"


@strawberry.type
class Query:
    field: IceCreamFlavour


schema = strawberry.Schema(query=Query)
```
