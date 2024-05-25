---
title: Missing arguments annotation Error
---

# Missing arguments annotation Error

## Description

This error is thrown when an argument is missing an annotation, for example the
following code will throw this error:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name) -> str:  #  <-- note name here is missing an annotation
        return f"hello {name}"


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry needs to know the type of every argument to be
able to generate the correct GraphQL type.

## How to fix this error

You can fix this error by adding an annotation to the argument, for example, the
following code will fix this error:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str) -> str:
        return f"hello {name}"


schema = strawberry.Schema(query=Query)
```
