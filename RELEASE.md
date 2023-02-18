Release type: minor

This releases adds support for Apollo Federation 2.1, 2.2 and 2.3.

This includes support for `@composeDirective` and `@interfaceObject`,
we expose directives for both, but we also have shortcuts, for example
to use `@composeDirective` with a custom schema directive, you can do
the following:

```python
@strawberry.federation.schema_directive(
    locations=[Location.OBJECT], name="cacheControl", compose=True
)
class CacheControl:
    max_age: int
```

The `compose=True` makes so that this directive is included in the supergraph
schema.

For `@interfaceObject` we introduced a new `@strawberry.federation.interface_object`
decorator. This works like `@strawberry.federation.type`, but it adds, the appropriate
directive, for example:

```python
@strawberry.federation.interface_object(keys=["id"])
class SomeInterface:
    id: strawberry.ID
```

generates the following type:

```graphql
type SomeInterface @key(fields: "id") @interfaceObject {
  id: ID!
}
```
