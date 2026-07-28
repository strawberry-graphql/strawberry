---
release type: patch
---

This release fixes federation `@key`, `@requires` and `@provides` directives
to use the schema's configured name converter, so the field names inside
them line up with the field names actually printed in the SDL.

Previously, `fields` selections on these directives were emitted as-is,
regardless of any name conversion applied to the fields themselves. With the
default camelCase conversion, this meant a snake_case Python field like
`my_key` was printed as `myKey` in the type but referenced as `my_key` in
`@key(fields: "my_key")` -- a mismatch that Apollo Federation composition
rejects.

`resolve_reference` now also receives keyword arguments matching each
field's Python name (e.g. `my_key`) instead of its GraphQL name (e.g.
`myKey`), matching how every other resolver in Strawberry receives its
arguments.

```python
@strawberry.federation.type(keys=["my_key"])
class Product:
    my_key: str

    @classmethod
    def resolve_reference(cls, my_key: str) -> "Product":
        return Product(my_key=my_key)
```

now prints `type Product @key(fields: "myKey")` (matching the `myKey` field
that's actually defined) and calls `resolve_reference(my_key=...)` instead
of raising `TypeError: resolve_reference() got an unexpected keyword
argument 'myKey'`.

If you were working around either of these bugs -- e.g. by writing
`keys=["myKey"]` directly, or by naming your `resolve_reference` parameters
after the GraphQL name instead of the Python name -- you'll need to update
those to use the field's Python name instead, as shown above.
