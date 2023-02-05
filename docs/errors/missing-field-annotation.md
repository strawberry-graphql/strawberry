---
title: Missing field annotation Error
---

# Missing field annotation Error

## Description

This error is thrown when a field on a class is missing an annotation, for
example the following code will throw this error:

```python
import strawberry


@strawberry.type
class Query:
    name: str
    age = strawberry.field(
        name="ageInYears"
    )  # note that here we don't have a type for this field


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry needs to know the type of every field for a type
to be able to generate the correct GraphQL type.

## How to fix this error

You can fix this error by adding an annotation to the field, for example, the
following code will fix this error:

```python
import strawberry


@strawberry.type
class Query:
    name: str
    age: int = strawberry.field(name="ageInYears")


schema = strawberry.Schema(query=Query)
```
