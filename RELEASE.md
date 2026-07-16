---
release type: patch
social_messages:
  x: >-
    {project_name} {version} applies a custom default_resolver to interface fields
    that return a mapping, picking the concrete type from __typename. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} fixes a custom default_resolver not being applied to
    fields typed as an interface: a mapping returned for such a field is now
    resolved to the concrete type named by its __typename.
---

This release fixes a custom `default_resolver` not being applied to fields typed
as an interface.

When a `default_resolver` returned a mapping (for example a `dict`) for a field
whose type is an interface, Strawberry could not determine the concrete type and
reported `Expected value of type '...'`. The concrete type is now selected from
the mapping's `__typename`, so interface fields work the same way non-interface
fields already do:

```python
@strawberry.interface
class UserInterface:
    name: str


@strawberry.type
class Client(UserInterface):
    company_name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> UserInterface:
        return {"name": "Patrick", "company_name": "company", "__typename": "Client"}


schema = strawberry.Schema(
    query=Query,
    types=[Client],
    config=StrawberryConfig(default_resolver=lambda obj, key: obj[key]),
)
```
