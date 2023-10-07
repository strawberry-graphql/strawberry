---
title: Invalid Argument Type Error
---

# Invalid Argument Type Error

## Description

This error is thrown when an argument is of the wrong type, it usually happens
when passing **unions** or **interfaces** as an argument, for example the
following code will throw this error:

```python
import strawberry

from typing import Union, Annotated


@strawberry.type
class TypeA:
    id: strawberry.ID


ExampleUnion = Annotated[Union[TypeA], strawberry.union("ExampleUnion")]


@strawberry.type
class Query:
    @strawberry.field
    def example(self, data: Example) -> str:
        return "this is an example"


schema = strawberry.Schema(query=Query)
```

## Using union types as arguments

The latest [GraphQL specification](https://spec.graphql.org/October2021/)
doesn't allow using unions as arguments. There's currently an
[RFC for adding a `oneOf` directive](https://github.com/graphql/graphql-spec/pull/825)
that might work for your use case, but it's not yet implemented in the spec and
Strawberry
