Release type: minor

This release adds support for adding descriptions to enum values.

### Example


```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value(
        "strawberry", description="Our favourite",
    )
    CHOCOLATE = "chocolate"


@strawberry.type
class Query:
    favorite_ice_cream: IceCreamFlavour = IceCreamFlavour.STRAWBERRY

schema = strawberry.Schema(query=Query)
```

This produces the following schema

```graphql
enum IceCreamFlavour {
  VANILLA

  """Our favourite."""
  STRAWBERRY
  CHOCOLATE
}

type Query {
  favoriteIceCream: IceCreamFlavour!
}
```
