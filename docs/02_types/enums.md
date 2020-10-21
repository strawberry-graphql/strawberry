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

and We should define queries. for example:


```python
@strawberry.type
class Query:
    @strawberry.field
    def best_Flavour(self, info) -> IceCreamFlavour:
        return cone(IceCreamFlavour.STRAWBERRY)
```

Defining the enum type above would produce like this schema in GraphQL:

```graphql
enum IceCreamFlavour {
  VANILLA
  STRAWBERRY
  CHOCOLATE
}
```

Then it can be queried by the user. Snakecase is turn camelcase in GraphQL. for example:

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

After that, We can use this enum type when defining another types.
Here is an example of define type using enum type:

```python
@strawberry.type
class Cone:
    flavour: IceCreamFlavour
    scoop: int
```

You should define Query for using cone.

```python
@strawberry.type
class Query:
    @strawberry.field
    def cone(self, info) -> Cone:
        return Cone(flavour=IceCreamFlavour.STRAWBERRY, scoop=4)
```

Then user can get cone's data. Here is query:

```graphql
query {
  cone {
    flavour
    scoop
  }
}
```

Here is result of executed query:

```graphql
{
  "data": {
    "cone": {
      "flavour": "STRAWBERRY",
      "scoop": 4
    }
  }
}
```

> **NOTE**: GraphQL types are not a map of name: value, like in python enums.
> Strawberry uses the name of the members of the enum to create the GraphQL
> type.

<AdditionalResources
  title="Enums"
  spec="https://spec.graphql.org/June2018/#sec-Enums"
  graphqlDocs="https://graphql.org/learn/schema/#enumeration-types"
/>
