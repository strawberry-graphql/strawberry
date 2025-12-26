Release type: minor

Deprecate passing a class to `strawberry.scalar()`. Use `scalar_map` in
`StrawberryConfig` instead for better type checking support.

```python
# Before (deprecated)
Base64 = strawberry.scalar(
    NewType("Base64", bytes),
    serialize=lambda v: base64.b64encode(v).decode(),
    parse_value=lambda v: base64.b64decode(v),
)
```

Instead, use `scalar_map` in `StrawberryConfig`:

```python
# Recommended
Base64 = NewType("Base64", bytes)

schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        scalar_map={
            Base64: strawberry.scalar(
                name="Base64",
                serialize=lambda v: base64.b64encode(v).decode(),
                parse_value=lambda v: base64.b64decode(v),
            )
        }
    ),
)
```

This release also removes internal scalar wrapper exports (`Date`, `DateTime`,
etc.) from `strawberry.schema.types.base_scalars`. Most users are likely not
using these, but if you were, a codemod is available to help with the migration:
`strawberry upgrade replace-scalar-wrappers .`
