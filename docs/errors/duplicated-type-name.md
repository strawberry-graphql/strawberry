---
title: Duplicated Type Name Error
---

# Duplicated Type Name Error

## Description

This error is thrown when you try to register two types with the same name in
the schema.

For example, the following code will throw this error:

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type(name="User")
class UserB:
    name: str


@strawberry.type
class Query:
    user: User
    user_b: UserB


schema = strawberry.Schema(query=Query)
```

## How to fix this error

To fix this error you need to make sure that all the types in your schema have
unique names. For example in our example above we can fix this error by changing
the `name` argument of the `UserB` type:

```python
import strawberry


@strawberry.type
class User:
    name: str


# Note: Strawberry will automatically use the name of the class
# if it is not provided, in this case we are passing the name
# to show how it works and how to fix the error
@strawberry.type(name="UserB")
class UserB:
    name: str


@strawberry.type
class Query:
    user: User
    user_b: UserB


schema = strawberry.Schema(query=Query)
```
