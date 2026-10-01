---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Pydantic models can now be used directly as
    GraphQL types, inputs and interfaces with strawberry.pydantic, including
    validation of inputs. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Pydantic v2 models can now be decorated
    directly with strawberry.pydantic.type, strawberry.pydantic.input and
    strawberry.pydantic.interface, so the same model defines your GraphQL schema
    and validates your inputs.
---

This release adds first-class support for Pydantic v2 models.

Pydantic models can now be decorated directly to become GraphQL types, inputs
and interfaces, without a separate Strawberry class:

```python
from pydantic import BaseModel, Field

import strawberry


@strawberry.pydantic.type
class User(BaseModel):
    id: strawberry.ID
    name: str = Field(description="The user's full name")
    password_hash: strawberry.Private[str]


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str = Field(min_length=1)
```

Inputs are validated by Pydantic when the arguments are converted. Invalid
inputs are reported as GraphQL errors with a `validationErrors` extension, or,
by returning `User | strawberry.pydantic.ValidationError` and registering
`strawberry.pydantic.PydanticValidationErrorHandler` in the schema's
`exception_handlers`, as typed results.

GraphQL field names come from the Python field names, as Pydantic aliases only
affect Pydantic's own (de)serialization: use
`Annotated[..., strawberry.field(name=...)]` to rename a field. Computed fields
are included, and deprecated fields are deprecated in GraphQL too.
Fields with a resolver can be added with `@strawberry.pydantic.field`, fields
can be customized with `Annotated[..., strawberry.field(...)]`, and
`strawberry.Private` or Pydantic's `Field(exclude=True)` hide a field from the
schema. See the [Pydantic integration docs](https://strawberry.rocks/docs/integrations/pydantic)
for everything that's supported.

This release also fixes objects cast with `strawberry.cast` not being resolved
when they're returned in a union.
