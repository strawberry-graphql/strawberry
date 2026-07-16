---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes a crash when a resolver argument of an input
    type used a constructed instance as its default value and the argument was
    omitted. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} fixes a `TypeError` crash that happened when a
    resolver argument of an input type used a constructed instance (e.g.
    `Pagination()`) as its default value and the argument was omitted. Such
    default instances are now passed through correctly instead of being treated
    as a mapping of field values.
---

This release fixes a crash when a resolver argument of an input type has a
constructed instance as its default value and the argument is omitted, for
example:

```python
@strawberry.input
class Pagination:
    limit: int = 10
    offset: int = 0


@strawberry.type
class Query:
    @strawberry.field
    def items(self, pagination: Pagination = Pagination()) -> str: ...
```

Calling `{ items }` previously raised `TypeError: argument of type
'Pagination' is not a container or iterable`, because the default instance
reached argument conversion as an already-built object rather than a mapping.
Such default instances are now passed through unchanged.
