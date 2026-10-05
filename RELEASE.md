---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Federation schemas now keep the
    description and directives of your Query type, and add a single
    @composeDirective for each composed directive.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes two federation schema
    issues: the description and directives of the root Query type, like
    @shareable, are no longer dropped, and directives defined with compose=True
    get a single @composeDirective instead of one for every place they're used.
---

This release fixes two issues with how federation schemas print the root
`Query` type and composed directives.

The description and directives of the `Query` type were dropped, because
`strawberry.federation.Schema` rebuilds that type to add the `_service` and
`_entities` fields. Directives like `@shareable` and composed custom directives
on `Query` are now kept, along with the `@link` and `@composeDirective` they
need:

```python
@strawberry.federation.type(shareable=True, description="The root query")
class Query:
    hello: str
```

Directives defined with `compose=True` also added one `@composeDirective` to the
schema for every place they were used, instead of one per directive:

```python
@strawberry.federation.schema_directive(
    locations=[Location.FIELD_DEFINITION], repeatable=True, compose=True
)
class Tag:
    name: str


@strawberry.type
class Query:
    a: str = strawberry.field(directives=[Tag(name="x")])
    b: str = strawberry.field(directives=[Tag(name="y")])
```

This schema used to print `@composeDirective(name: "@tag")` twice. It now prints
it once.
