---
title: Enums
path: /docs/types/enums
---

# Enums

Enums are a special kind of type that is restrict to a particular set of values.

For example, we have a few options of ice cream available, and we want to allow
user to choose only from those options.

Strawberry supports defining enums using enums from python's standard library.
Here's a quick tutorial on how to create an enum type in Strawberry:

First, create a new class for the new type, which extends class Enum:

```python
class IceCreamFlavour(Enum):
```

Then, list options as variables in that class:

```python
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
```

Finally we need to register our class as a strawberry type. It's done with the
`strawberry.enum` decorator:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
```

After that, we can use this enum type when defining types:

```python
@strawberry.type
class Cone:
    flavour: IceCreamFlavour
    scoops: int
```

and queries:

```python
@strawberry.type
class Query:
    @strawberry.field
    def best_flavour(self, info) -> IceCreamFlavour:
        return IceCreamFlavour.STRAWBERRY
```

Defining the enum type above would produce this schema:

```graphql
enum IceCreamFlavour {
  VANILLA
  STRAWBERRY
  CHOCOLATE
}
```

Then it can be queried by the user, for example:

```graphql
query {
  cone(IceCreamFlavour: STRAWBERRY)
}
```

> **NOTE**: GraphQL types are not a map of name: value, like in python enums.
> Strawberry uses the name of the members of the enum to create the GraphQL
> type.

You can also refer to the GraphQL documentation about Enum types here:
https://graphql.org/learn/schema/#enumeration-types GraphQL specification of
enum types is here: https://spec.graphql.org/June2018/#sec-Enums
