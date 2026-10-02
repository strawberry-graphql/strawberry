---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Objects cast with strawberry.cast, like ORM
    rows, can now be returned in unions.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes objects cast with
    strawberry.cast not being resolved when they're returned in a union, so
    resolvers can return ORM rows and other look-alike objects for union types.
---

This release fixes objects cast with `strawberry.cast` not being resolved when
they're returned in a union.

Resolvers can return objects that aren't instances of a union's types, like rows
of an ORM, by casting them to the type they represent:

```python
@strawberry.type
class Query:
    @strawberry.field
    def latest_media(self) -> Audio | Video:
        return strawberry.cast(Video, db.media.latest())
```

Casts to a generic type work too, like `strawberry.cast(Edge, row)` for an
`Edge[int]` member, also when it's returned through an interface that `Edge`
implements. The cast takes precedence over the types' `is_type_of`, and
when it doesn't match exactly one type of the union, for example a cast to an
interface, the object is resolved as before.
