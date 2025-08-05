---
title: Scalar already registered Error
---

# Scalar already registered Error

## Description

This error is thrown when trying to use a scalar that is already registered.
This usually happens when using the same name for different scalars, for example
the following code will throw this error:

```python
import strawberry

MyCustomScalar = strawberry.scalar(
    str,
    name="MyCustomScalar",
)

MyCustomScalar2 = strawberry.scalar(
    int,
    name="MyCustomScalar",
)


@strawberry.type
class Query:
    scalar_1: MyCustomScalar
    scalar_2: MyCustomScalar2


strawberry.Schema(Query)
```

This happens because different types in Strawberry (and GraphQL) cannot have the
same name.

<Note>
  This error might happen also when trying to defined a scalar with the same
  name as a type.
</Note>

## How to fix this error

You can fix this error by either reusing the existing scalar, or by changing the
name of one of them, for example in this code we renamed the second scalar:

```python
import strawberry

MyCustomScalar = strawberry.scalar(
    str,
    name="MyCustomScalar",
)

MyCustomScalar2 = strawberry.scalar(
    int,
    name="MyCustomScalar2",
)


@strawberry.type
class Query:
    scalar_1: MyCustomScalar
    scalar_2: MyCustomScalar2


strawberry.Schema(Query)
```
