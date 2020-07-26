---
title: Enums
path: /docs/types/enums
---

# Enums

Enums are used for listing items, that can be used as values in other places. 
It's useful when we need to provide user with options to chose from. 

For example, we have a few options of ice cream available, and would like to allow user to choose only from those options.

Enum is a custom type, defined by a developer. 

To define an enum type, we need to follow these steps:

1. Create a new class for the new type, which extends class Enum:

    ```class IceCreamFlavour(Enum):```

2. Next, list options as variables in that class:

   ```
   class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
   ```

3. Then we need to register our class as a strawberry type. It's done with a decorator `strawberry.enum`:

    ```
    @strawberry.enum
    class IceCreamFlavour(Enum):
        VANILLA = "vanilla"
        STRAWBERRY = "strawberry"
        CHOCOLATE = "chocolate"
    ```

After that, we can use this enum type when defining types:

```
@strawberry.type
class Cone:
    flavour: IceCreamFlavour
    scoops: int
```

and queries:

```
@strawberry.type
class Query:
    @strawberry.field
    def best_flavour(self, info) -> IceCreamFlavour:
        return IceCreamFlavour.STRAWBERRY
```

Defining the enum type above would produce this schema:

```
enum IceCreamFlavour {
  VANILLA
  STRAWBERRY
  CHOCOLATE
}
```

Then it can be queried by the user, for example:

```
query {
  cone(IceCreamFlavour: STRAWBERRY)
}
```

You can also refer to the GraphQL documentation about Enu, types here: https://graphql.org/learn/schema/#enumeration-types 
