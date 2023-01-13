---
title: Missing return annotation Error
---

# Missing return annotation Error

## Description

This error is thrown when a resolver and it's corresponding field don't have a
return annotation, for example the following code will throw this error:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def example(self):
        return "this is an example"


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry needs to know the return type of the resolver to
be able to generate the correct GraphQL type.

## How to fix this error

You can fix this error by adding a return annotation to the resolver, for
example, the following code will fix this error:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def example(self) -> str:
        return "this is an example"


schema = strawberry.Schema(query=Query)
```
