---
release type: minor
---

This release adds first-class support for Pydantic v2 models, with
`strawberry.pydantic`. It requires Pydantic 2.11 or newer.

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

Pydantic owns nested validation. Strawberry converts names and scalars and
transports GraphQL lists as tuples for tuple fields, including in strict mode;
it does not prevalidate nested models for validators that bypass or replace
Pydantic's usual validation. Validator `ValueError`s expose their original
message without Pydantic's generated `"Value error, "` prefix; other messages
are preserved. Error locations contain strings, including list indexes, in
both typed results and GraphQL error extensions. The error's `input` property
is omitted and exception chaining is suppressed, but messages may still
contain submitted values, even for built-in errors.

Explicit field defaults use Strawberry's ordinary schema default machinery,
including `None` as `null` and model instances as input objects. Default
factories are Pydantic-owned and run per request when the field is omitted,
including factories that need already validated data. Their fields are nullable
in GraphQL to allow omission, without publishing a schema default.

Only explicitly set fields of a model argument default are printed in that
default. GraphQL can supply additional field defaults during input coercion, so
`model_fields_set` is not guaranteed to survive a round trip unchanged, and
`model_dump(exclude_unset=True)` is not a record of only client-submitted
fields.

Nullable fields without a default, like `nickname: str | None`, are optional for
clients, like in other input types: Pydantic gets `None` for them when they're
left out, as if the client had sent `null`.

GraphQL field names come from the Python field names, as Pydantic aliases only
affect Pydantic's own (de)serialization: use
`Annotated[..., strawberry.field(name=...)]` to rename a field. Computed fields
are included, and deprecated fields are deprecated in GraphQL too. Fields with a
resolver can be added with `@strawberry.pydantic.field`, fields can be
customized with `Annotated[..., strawberry.field(...)]`, `strawberry.Private`
hides a field from the schema, and Pydantic's `Field(exclude=True)` hides it
from output types (inputs still accept it). See the
[Pydantic integration docs](https://strawberry.rocks/docs/integrations/pydantic)
for everything that's supported.

Generic models work like generic Strawberry types: decorate the generic model,
and use its parametrizations directly, like `Page[User]`, which is named
`UserPage` in the schema.

Each model class has one GraphQL role: use separate subclasses for output types
and inputs. Forward references support self-references, same-module models and
explicit `strawberry.lazy()` references. If unresolved references affect field
metadata or GraphQL mappings, call `model_rebuild()` before decorating:
rebuilding afterward does not refresh captured GraphQL fields or mappings.

GraphQL resolves fields from the model's attributes, so Pydantic's serializers
don't apply to it. Instead of silently ignoring them, types and interfaces whose
exposed fields have serializers, or that have a model serializer, raise an
error. This includes `PlainSerializer` and `WrapSerializer` in computed fields'
return annotations. There is no option to bypass this check; use private or
excluded fields and explicit GraphQL resolvers to hide or transform values.

Pydantic types can also extend regular Strawberry types and implement regular
`@strawberry.interface`s, including their `@strawberry.field` methods, as long
as the Pydantic model comes first in the bases:

```python
@strawberry.interface
class Node:
    id: strawberry.ID

    @strawberry.field
    def display_name(self) -> str:
        return f"Node {self.id}"


@strawberry.pydantic.type
class Product(BaseModel, Node):
    title: str
```

This includes `relay.Node`, with a `relay.NodeID` field and a `resolve_nodes`
class method, like on regular Strawberry types.

Resolver functions can be reused across Pydantic fields and models, with
independent names, descriptions and permissions for each decoration.

Resolvers also accept bound methods and typed callable objects, including async
callables, and the `resolver=...` spelling. Their Python binding behavior is
preserved.

Explicit `scalar_map` entries take precedence over automatic Pydantic scalar
mappings. Undecorated models can be used as custom scalars; missing model
registration is checked when building the schema rather than during decoration.
Regular Strawberry fields returning undecorated Pydantic models also raise the
contextual `UnregisteredPydanticTypeError`, rather than a generic unexpected-type
error, even without explicitly importing `strawberry.pydantic` first.
Upload fields use Pydantic's validation, including custom validators, instead
of being rejected by their annotation. Defaults in Strawberry `Annotated`
metadata raise a clear error: defaults must be declared on the Pydantic field.

The experimental integration, `strawberry.experimental.pydantic`, keeps working
as before, next to `strawberry.pydantic`. The two integrations can't use each
other's types, so models that reference each other need to use the same
integration, or have a type from both.
