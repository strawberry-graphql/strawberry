---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes schema generation crashing when a Pydantic
    field uses `SkipJsonSchema[None]` in a union — the field is now correctly an
    optional. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} fixes a bug where a Pydantic model field using
    `SkipJsonSchema[None]` in a union (e.g. `str | SkipJsonSchema[None]`)
    crashed schema generation with `InvalidUnionTypeError`. The annotated `None`
    is now treated as null, so the field becomes an optional as expected.
---

This release fixes schema generation raising `InvalidUnionTypeError` when a
Pydantic model field uses `SkipJsonSchema[None]` in a union type, for example:

```python
class ModelA(BaseModel):
    field_a: str | SkipJsonSchema[None] = None
```

`SkipJsonSchema[None]` expands to `Annotated[None, SkipJsonSchema()]`, and the
annotated `None` was not recognised as `None`, so the field was treated as a
(invalid) GraphQL union of `str` and `None` instead of an optional `str`. The
annotation metadata is now stripped during conversion, so the field correctly
becomes a nullable `String`.
