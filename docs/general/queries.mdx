---
title: Queries
---

# Queries

In GraphQL you use queries to fetch data from a server. In Strawberry you can
define the data your server provides by defining query types.

By default all the fields the API exposes are nested under a root Query type.

This is how you define a root query type in Strawberry:

```python
@strawberry.type
class Query:
    name: str


schema = strawberry.Schema(query=Query)
```

This creates a schema where the root type Query has one single field called
name.

As you notice we don't provide a way to fetch data. In order to do so we need to
provide a `resolver`, a function that knows how to fetch data for a specific
field.

For example in this case we could have a function that always returns the same
name:

```python
def get_name() -> str:
    return "Strawberry"


@strawberry.type
class Query:
    name: str = strawberry.field(resolver=get_name)


schema = strawberry.Schema(query=Query)
```

So now, when requesting the name field, the `get_name` function will be called.

Alternatively a field can be declared using a decorator:

```python
@strawberry.type
class Query:
    @strawberry.field
    def name(self) -> str:
        return "Strawberry"
```

## Arguments

GraphQL fields can accept arguments, usually to filter out or retrieve specific
objects:

```python
FRUITS = [
    "Strawberry",
    "Apple",
    "Orange",
]


@strawberry.type
class Query:
    @strawberry.field
    def fruit(self, startswith: str) -> str | None:
        for fruit in FRUITS:
            if fruit.startswith(startswith):
                return fruit
        return None
```

Additional metadata can be added to arguments, for example a custom name and
description using `strawberry.argument` with
[typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated):

```python
@strawberry.type
class Query:
    @strawberry.field
    def fruits(
        self,
        is_tasty: Annotated[
            bool | None,
            strawberry.argument(
                description="Filters out fruits by whenever they're tasty or not",
                deprecation_reason="isTasty argument is deprecated, "
                "use fruits(taste:SWEET) instead",
            ),
        ] = None,
    ) -> list[str]: ...
```
