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

The decorator syntax supports specifying a `graphql_type` for cases when the
return type of the function does not match the GraphQL type:

```python
class User:
    id: str
    name: str

    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

@strawberry.type(name="User")
class UserType:
    id: strawberry.ID
    name: str

@strawberry.type
class Query:
    @strawberry.field(graphql_type=UserType)
    def user(self) -> User
        return User(id="ringo", name="Ringo")
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
