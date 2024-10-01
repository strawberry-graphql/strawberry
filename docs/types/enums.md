---
title: Enums
---

# Enums

Enums are a special kind of type that is restricted to a particular set of
values.

For example, we have a few options of ice cream available, and we want to allow
user to choose only from those options.

Strawberry supports defining enums using enums from python's standard library.
Here's a quick tutorial on how to create an enum type in Strawberry:

First, create a new class for the new type, which extends class Enum:

```python
from enum import Enum


class IceCreamFlavour(Enum): ...
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

<Note>

In some cases you already have an enum defined elsewhere in your code. You can
safely use it in your schema and strawberry will generate a default graphql
implementation of it.

The only drawback is that it is not currently possible to configure it
(documentation / renaming or using `strawberry.enum_value` on it).

</Note>

Let's see how we can use Enums in our schema.

```python
@strawberry.type
class Query:
    @strawberry.field
    def best_flavour(self) -> IceCreamFlavour:
        return IceCreamFlavour.STRAWBERRY
```

Defining the enum type above would produce this schema in GraphQL:

```graphql
enum IceCreamFlavour {
  VANILLA
  STRAWBERRY
  CHOCOLATE
}
```

Here's an example of how you'd use this newly created query:

```graphql
query {
  bestFlavour
}
```

Here is result of executed query:

```graphql
{
  "data": {
    "bestFlavour": "STRAWBERRY"
  }
}
```

We can also use enums when defining object types (using `strawberry.type`). Here
is an example of an object that has a field using an Enum:

```python
@strawberry.type
class Cone:
    flavour: IceCreamFlavour
    num_scoops: int


@strawberry.type
class Query:
    @strawberry.field
    def cone(self) -> Cone:
        return Cone(flavour=IceCreamFlavour.STRAWBERRY, num_scoops=4)
```

And here's an example of how you'd use this query:

```graphql
query {
  cone {
    flavour
    numScoops
  }
}
```

Here is result of executed query:

```graphql
{
  "data": {
    "cone": {
      "flavour": "STRAWBERRY",
      "numScoops": 4
    }
  }
}
```

<Note>

GraphQL types are not a map of name: value, like in python enums. Strawberry
uses the name of the members of the enum to create the GraphQL type.

</Note>

You can also deprecate enum value. To do so you need more verbose syntax using
`strawberry.enum_value` and `deprecation_reason`. You can mix and match string
and verbose syntax.

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    CHOCOLATE = "chocolate"
    STRAWBERRY = strawberry.enum_value(
        "strawberry", deprecation_reason="Let's call the whole thing off"
    )
```
