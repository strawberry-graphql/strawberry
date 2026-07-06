---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes `print_schema` emitting duplicate type definitions when a type is used both as a schema directive field and elsewhere in the schema.
  linkedin: >-
    {project_name} {version} fixes a bug where `print_schema` produced invalid SDL by printing a type twice when it was referenced both by a schema directive field and as a regular schema type. Upgrade to get valid, spec-compliant SDL output.
---

This release fixes a bug where `print_schema` would emit a type definition
twice when the same type (for example an enum) was referenced both as a schema
directive field and elsewhere in the schema. The duplicated definition produced
invalid SDL that violates the GraphQL spec and is rejected by `graphql-core`'s
`build_schema`.

For example, the following schema now prints `enum Role` only once:

```python
import enum

import strawberry
from strawberry.schema_directive import Location


@strawberry.enum
class Role(enum.Enum):
    EDITOR = "editor"
    VIEWER = "viewer"


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class RequiresRole:
    roles: list[Role]


@strawberry.type
class Query:
    secret: str = strawberry.field(directives=[RequiresRole(roles=[Role.EDITOR])])

    @strawberry.field
    def assign(self, role: Role) -> bool:
        return True
```
