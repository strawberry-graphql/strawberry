---
title: Invalid Superclass Interface Error
---

# Invalid Superclass Interface Error

## Description

This error is thrown when you define a class that has the `strawberry.input`
decorator but also inherits from one or more classes with the
`strawberry.interface` decorator. The underlying reason for this is that in
GraphQL, input types cannot implement interfaces. For example, the following
code will throw this error:

```python
import strawberry


@strawberry.interface
class SomeInterface:
    some_field: str


@strawberry.input
class SomeInput(SomeInterface):
    another_field: int
```
