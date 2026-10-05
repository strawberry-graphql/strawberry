---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Federation schemas no longer drop Query
    fields named service, and a Query can define its own _service or _entities
    field. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes federation schemas
    removing Query fields that shared a Python name with Strawberry's internal
    federation resolvers, like service, and lets a Query define its own
    _service or _entities field.
---

This release fixes how federation schemas add the `_service` and `_entities`
fields to the `Query` type.

Fields of the `Query` type were matched with these fields by their Python name
instead of their GraphQL name. A `Query` field named `service` was removed from
the schema, with only a "Query has overridden fields: service" warning:

```python
@strawberry.type
class Query:
    @strawberry.field
    def service(self) -> str:  # was missing from the schema
        return "service"


schema = strawberry.federation.Schema(query=Query)
```

Fields like this are now kept. A `Query` that defines its own `_service` or
`_entities` field now uses it instead of the one Strawberry adds. Before, doing
this with your own `_Service` type failed with a `DuplicatedTypeName` error:

```python
@strawberry.type(name="_Service")
class CustomService:
    sdl: str


@strawberry.type
class Query:
    @strawberry.field(name="_service")
    def custom_service(self) -> CustomService:
        return CustomService(sdl=load_sdl())
```
