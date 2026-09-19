---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes input type instances
    used as default values for arguments and input fields. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes input type instances
    used as default values for arguments and input fields, so they work at
    execution time and show up in introspection.
---

This release fixes input type instances used as default values for resolver
arguments and input fields.

```python
@strawberry.input
class Pagination:
    limit: int = 10
    offset: int = 0


@strawberry.type
class Query:
    @strawberry.field
    def numbers(self, pagination: Pagination = Pagination(limit=5)) -> list[int]:
        return list(range(pagination.offset, pagination.offset + pagination.limit))
```

Executing `{ numbers }` now passes a fresh `Pagination(limit=5, offset=0)` to
the resolver, and the default is reported by introspection as
`{limit: 5, offset: 0}`. The same applies to input fields declared with
`strawberry.field(default_factory=...)` returning an input instance.
