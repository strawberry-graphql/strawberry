Release type: minor

This release adds support for custom names in enum values using the `name` parameter in `strawberry.enum_value`.

This allows you to specify a different name for an enum value in the GraphQL schema while keeping the original Python enum member name. For example:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    CHOCOLATE_COOKIE = strawberry.enum_value("chocolate", name="chocolateCookie")
```

This will produce a GraphQL schema with the custom name:

```graphql
enum IceCreamFlavour {
    VANILLA
    chocolateCookie
}
```
