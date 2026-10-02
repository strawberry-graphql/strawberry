---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes unions that got the same
    name as another union with different types: they now raise an error when the
    schema is built, instead of failing at runtime.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes unions that got the same
    name as another union with different types, like Ok | Error with two
    different Error types. Strawberry used to silently reuse the first union, so
    resolving the second one failed at runtime. The schema now raises
    DuplicatedTypeName when it's built.
---

This release fixes unions with the same name but different types.

Strawberry reused a union by its name without checking its types, so a union
whose generated name matched another union, for example `Ok | Error` with two
different `Error` types, was silently replaced by the first one, and returning
the second `Error` failed at runtime:

```python
@strawberry.type
class Query:
    @strawberry.field
    def a(self) -> Ok | Error: ...

    @strawberry.field
    def b(self) -> Ok | OtherError: ...  # also named OkError
```

Building this schema now raises `DuplicatedTypeName`, like other types with the
same name do. Explicitly named unions, such as
`Annotated[A | B, strawberry.union("AB")]`, are checked too.
