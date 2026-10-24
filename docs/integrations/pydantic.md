---
title: Pydantic support
---

# Pydantic support

Strawberry provides first-class support for [Pydantic](https://pydantic.dev/)
models, allowing you to directly decorate your Pydantic `BaseModel` classes to
create GraphQL types without writing code twice.

## Installation

```bash
pip install 'strawberry-graphql[pydantic]'
```

`strawberry.pydantic` requires Pydantic 2.11 or newer. If an older version is
installed, upgrade it with `pip install -U 'pydantic>=2.11'`. Pydantic v1 models
are only supported by the
[experimental integration](#experimental-pydantic-support).

## Basic Usage

The simplest way to use Pydantic with Strawberry is to decorate your Pydantic
models directly:

```python
import strawberry
from pydantic import BaseModel


@strawberry.pydantic.type
class User(BaseModel):
    id: int
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> User:
        return User(id=1, name="John", email="john@example.com")


schema = strawberry.Schema(query=Query)
```

This automatically creates a GraphQL type that includes all fields from your
Pydantic model.

Returning an undecorated Pydantic model from a regular `@strawberry.field`
raises
[`UnregisteredPydanticTypeError`](../errors/unregistered-pydantic-type.md) when
the schema is built, identifying the field and the missing decorator. Use
`@strawberry.pydantic.type`, or explicitly map the model to a custom scalar.

## Type Decorators

### `@strawberry.pydantic.type`

Creates a GraphQL object type from a Pydantic model:

```python
@strawberry.pydantic.type
class User(BaseModel):
    name: str
    age: int
    is_active: bool = True
```

Like with `@strawberry.type`, resolvers can return other objects with the same
attributes, like rows of an ORM. Where Strawberry needs to know their type, in
unions and for types implementing interfaces, wrap them with `strawberry.cast`:

```python
@strawberry.mutation
def create_user(self, input: CreateUserInput) -> User | ValidationError:
    row = db.users.insert(name=input.name)

    return strawberry.cast(User, row)
```

Define an `is_type_of` class method on the model to only accept some objects.

### `@strawberry.pydantic.input`

Creates a GraphQL input type from a Pydantic model:

```python
@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    age: int


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User:
        return User(name=input.name, age=input.age)
```

Pass `one_of=True` to create a
[`oneOf` input](../types/input-types.md#one-of-input-types), where clients set
exactly one field. Its fields must be nullable and have no explicit defaults,
including `None`, like ordinary Strawberry `oneOf` inputs:

```python
@strawberry.pydantic.input(one_of=True)
class UserBy(BaseModel):
    id: strawberry.ID | None
    email: str | None
```

### `@strawberry.pydantic.interface`

Creates a GraphQL interface from a Pydantic model:

```python
@strawberry.pydantic.interface
class Node(BaseModel):
    id: strawberry.ID


@strawberry.pydantic.type
class User(Node):
    name: str
```

Types implement a Pydantic interface by subclassing it, and inherit its fields.

They can also implement a regular `@strawberry.interface`, including its fields
with a resolver, by extending it after `BaseModel`:

```python
@strawberry.interface
class Named:
    name: str

    @strawberry.field
    def display_name(self) -> str:
        return self.name.title()


@strawberry.pydantic.type
class Product(BaseModel, Named):
    price: float
```

The Pydantic model has to come first: the interface's `__init__` would otherwise
replace Pydantic's, so listing the interface first raises a
[`StrawberryBaseBeforeModelError`](../errors/strawberry-base-before-model.md).

## Configuration Options

All decorators accept optional configuration parameters:

```python
@strawberry.pydantic.type(
    name="CustomUser",  # Override the GraphQL type name
    description="A user in the system",  # Add type description
)
class User(BaseModel):
    name: str
    age: int
```

They also take `directives`, a list of
[schema directives](../types/schema-directives.md) for the type, like the
[federation](#federation) ones.

To use the same model as a GraphQL type and as an input, decorate a subclass, as
a model can only be decorated once:

```python
@strawberry.pydantic.type
class Address(BaseModel):
    street: str
    city: str


@strawberry.pydantic.input
class AddressInput(Address):
    pass
```

This doesn't work for an interface, or for a type that implements one, as inputs
can't implement interfaces: an input that subclasses them raises an
[`InvalidSuperclassInterfaceError`](../errors/invalid-superclass-interface.md).
Move the fields to share to an undecorated base model instead, and extend it
from both the output type and the input:

```python
@strawberry.pydantic.interface
class Node(BaseModel):
    id: strawberry.ID


class UserBase(BaseModel):
    name: str
    email: str


@strawberry.pydantic.type
class User(UserBase, Node):
    pass


@strawberry.pydantic.input
class UserInput(UserBase):
    pass
```

## Field Features

### Field Descriptions

Pydantic field descriptions are automatically preserved in the GraphQL schema:

```python
from pydantic import Field


@strawberry.pydantic.type
class User(BaseModel):
    name: str = Field(description="The user's full name")
    age: int = Field(description="The user's age in years")
```

### Field Names and Aliases

GraphQL field names come from the Python field names, like with
`@strawberry.type`. Pydantic aliases describe how the model is (de)serialized,
for example for a REST API, so they are not used in the GraphQL schema (unlike
in the [experimental integration](#moving-from-the-experimental-integration)).
Use `strawberry.field(name=...)` to rename a field:

```python
from typing import Annotated

from pydantic import Field


@strawberry.pydantic.type
class User(BaseModel):
    user_name: Annotated[str, Field(alias="user-name")]  # userName in GraphQL
    age: Annotated[int, strawberry.field(name="yearsOld")]
```

This also applies to fields named after Python keywords, which are usually
aliased: `from_: Annotated[date, Field(alias="from")]` is called `from_` in
GraphQL, unless it is renamed with
`Annotated[date, Field(alias="from"), strawberry.field(name="from")]`.

Inputs are validated by field name too, so validators with `mode="before"`
receive the data keyed by Python field names, not by aliases. A model shared
with a REST API that reads aliased keys in a `before` validator needs to handle
both, or use an `after` validator instead.

### Computed Fields

Pydantic's computed fields are part of the GraphQL type, like they are part of
`model_dump()`, with their description or the property's docstring as
description:

```python
from typing import Annotated

from pydantic import computed_field

from strawberry.scalars import JSON


@strawberry.pydantic.type
class User(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def settings(self) -> Annotated[dict, strawberry.field(graphql_type=JSON)]:
        return {"theme": "dark"}

    @computed_field
    @property
    def risk_score(self) -> strawberry.Private[int]:
        return 42
```

Like other fields, they can be customized with `strawberry.field()` in their
return type, and hidden with `strawberry.Private`. Pass `include_computed=False`
to the decorator to leave all of them out.

A subclass can override an inherited computed field with another computed field
or a property, or replace it with a field with a resolver (see
[Resolver Fields](#resolver-fields)). Overriding it with a method raises an
[`UnsupportedFieldOverrideError`](../errors/unsupported-field-override.md), as
Pydantic would use the method itself as the value of the field.

### Deprecated Fields

Fields deprecated with Pydantic's `Field(deprecated=...)` or
`computed_field(deprecated=...)` are deprecated in the GraphQL schema too.
Pydantic still emits its `DeprecationWarning` when the field is read, including
when it's resolved.

```python
@strawberry.pydantic.type
class User(BaseModel):
    name: str
    full_name: str = Field(deprecated="Use name")


@strawberry.pydantic.input
class UserInput(BaseModel):
    name: str
    full_name: str = Field(default="", deprecated="Use name")
```

```graphql
type User {
  name: String!
  fullName: String! @deprecated(reason: "Use name")
}

input UserInput {
  name: String!
  fullName: String! = "" @deprecated(reason: "Use name")
}
```

Like on other input types, only input fields that clients can omit can be
deprecated: fields with a default, or nullable ones. GraphQL doesn't allow
deprecating required input fields, so deprecating `name` above would make the
schema fail to build with
`Required input field UserInput.name cannot be deprecated.`

### Default Values and Omitted Fields

Input fields with a default can be omitted by clients. Explicit Pydantic field
defaults use Strawberry's ordinary schema default machinery, including `None` as
`null` and model instances as input objects. Defaults must be representable by
the field's GraphQL type; they aren't classified by their Python type or
validated by Pydantic before schema printing:

```python
import uuid

from pydantic import BaseModel, Field


@strawberry.pydantic.input
class SearchInput(BaseModel):
    query: str
    page_size: int = 20
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tag: str | None = None
```

```graphql
input SearchInput {
  query: String!
  pageSize: Int! = 20
  requestId: UUID
  tag: String = null
}
```

Default factories are Pydantic's responsibility. They are not called to build
the schema or published as schema defaults. Their fields are nullable in GraphQL
so clients can omit them, and Pydantic calls the factory for each request that
omits the field. This includes factories that receive already validated field
data. This differs from defaults on ordinary Strawberry inputs. An explicit
`null` is validated by Pydantic like any other supplied value; it does not
invoke the factory.

A nullable field without a default, like `nickname: str | None`, is optional for
clients too, as GraphQL requires for nullable input fields. When a client leaves
it out, Pydantic gets `None` for it, as if the client had sent `null`: the field
is part of `model_fields_set`, and validators see `None`.

GraphQL fills in defaults published in the schema before Pydantic validates the
input. These values can therefore be part of `model_fields_set` even when the
client omitted them. Do not use `model_dump(exclude_unset=True)` as a record of
only client-submitted fields, or rely on it to distinguish omission from
explicit `null` for partial updates.

When a model is an argument default, only its explicitly set fields are emitted
in the printed argument default. For example:

```python
@strawberry.pydantic.input
class UpdateUserInput(BaseModel):
    name: str | None = None
    bio: str | None = None
```

The printed default of `input: UpdateUserInput = UpdateUserInput(name="Ada")` is
`{ name: "Ada" }`. This does not guarantee that the resolver receives the same
`model_fields_set`: GraphQL field defaults may supply other fields. Like
client-supplied inputs, argument defaults are validated for each request that
uses them.

`strawberry.Maybe` can't be used in Pydantic inputs (Pydantic raises an error
for it when the model is defined). Use a regular Strawberry input with
`strawberry.Maybe` if you need to distinguish omission from explicit `null`.

### Private Fields

You can use `strawberry.Private` to mark fields that should not be exposed in
the GraphQL schema but are still accessible in your Python code:

```python
import strawberry


@strawberry.pydantic.type
class User(BaseModel):
    id: int
    name: str
    password: strawberry.Private[str]  # Not exposed in GraphQL
    email: str
```

This generates a GraphQL schema with only the public fields:

```graphql
type User {
  id: Int!
  name: String!
  email: String!
}
```

Private fields are still part of the model, so they can be used by resolvers:

```python
@strawberry.pydantic.type
class User(BaseModel):
    name: str
    password_hash: strawberry.Private[str]

    @strawberry.pydantic.field
    def has_password(self) -> bool:
        return bool(self.password_hash)
```

Fields excluded from Pydantic's serialization with `Field(exclude=True)` are not
exposed on GraphQL types and interfaces either:

```python
from pydantic import BaseModel, Field


@strawberry.pydantic.type
class ApiClient(BaseModel):
    name: str
    api_key: str = Field(exclude=True)  # Not exposed in GraphQL
```

Input types are not affected: clients can still send fields marked with
`exclude=True`.

Other serialization settings don't apply to GraphQL: output fields are resolved
from the model's attributes, not from `model_dump()`, so serialization aliases
are ignored. Serializers are often used to hide or redact values, so instead of
ignoring them, types and interfaces with serializers on their exposed fields
(`field_serializer`, `PlainSerializer` or `WrapSerializer`),
`Field(exclude_if=...)` or a `model_serializer` raise an
[`IgnoredSerializerError`](../errors/ignored-serializer.md). This includes
`PlainSerializer` and `WrapSerializer` in computed fields' return annotations.
There is no configuration option to bypass this check. To hide or redact a
value, use `strawberry.Private`, `Field(exclude=True)` or a
[resolver field](#resolver-fields):

```python
@strawberry.pydantic.type
class Customer(BaseModel):
    name: str
    email: strawberry.Private[str]

    @strawberry.pydantic.field
    def masked_email(self) -> str:
        return f"{self.email[0]}***"
```

Pydantic's `SecretStr` fields are exposed as strings with their masked value,
`"**********"`, and `SecretBytes` fields aren't supported yet. Secrets usually
don't belong in the schema at all, so mark them with `strawberry.Private`:

```python
from pydantic import BaseModel, SecretBytes, SecretStr


@strawberry.pydantic.type
class Account(BaseModel):
    username: str
    password: strawberry.Private[SecretStr]
    signing_key: strawberry.Private[SecretBytes]
```

### Resolver Fields

Pydantic doesn't allow `strawberry.field` in a model, so use
`strawberry.pydantic.field` to add fields with a resolver. It takes the field
options of `strawberry.field`, like `name`, `description`, `permission_classes`
or `graphql_type`:

```python
@strawberry.pydantic.type
class User(BaseModel):
    id: strawberry.ID
    name: str

    @strawberry.pydantic.field
    def greeting(self, punctuation: str = "!") -> str:
        return f"Hi {self.name}{punctuation}"

    @strawberry.pydantic.field(permission_classes=[IsAuthenticated])
    async def posts(self, info: strawberry.Info, first: int = 10) -> list[Post]:
        posts = await info.context.loaders.posts_by_user.load(self.id)

        return posts[:first]
```

The resolvers stay regular methods of the model, so they can be combined with
other decorators, like `@staticmethod`, `@classmethod` or `@functools.cache`
(which needs a hashable model, for example with
`model_config = ConfigDict(frozen=True)`). They are inherited from base models
and from Pydantic interfaces, and the field is named after the attribute, so
`label = strawberry.pydantic.field(get_label)` adds a `label` field.
`strawberry.pydantic.field(resolver=get_label, description="A label")` also
works. Resolvers can be functions, bound methods, partials or typed callable
objects, including asynchronous ones. Bound methods and callable objects keep
their calling convention: calling them through a model does not inject another
`self`. Pydantic's mypy plugin reports this form as an untyped field, so prefer
the decorator form if you use it, or add `# type: ignore[pydantic-field]`.

The same resolver can be used by multiple fields, including on different models.
Each call to `strawberry.pydantic.field` creates its own method wrapper, so
names, descriptions and permissions are independent without changing the
original function.

To override an inherited field with a resolver, decorate the new method with
`@strawberry.pydantic.field` too. Overriding it with a method that isn't
decorated would remove the field, so it raises an
[`UnsupportedFieldOverrideError`](../errors/unsupported-field-override.md)
instead.

Input types can't have fields with a resolver, and defining one raises a
[`ResolverFieldOnInputError`](../errors/resolver-field-on-input.md). The ones
inherited from a base model, for example one shared with an output type, are
ignored.

`strawberry.pydantic.field` is only for fields with a resolver. To customize a
field of the model, use `strawberry.field()` in its annotation instead, like
`age: Annotated[int, strawberry.field(name="yearsOld")]` (see
[Field Directives and Customization](#field-directives-and-customization)):
using `strawberry.pydantic.field` there raises a
[`MisplacedFieldError`](../errors/misplaced-field.md).

`@strawberry.field` can't be used in a Pydantic model: Pydantic raises
`PydanticUserError: A non-annotated attribute was detected` when the model is
defined. Use `@strawberry.pydantic.field` instead.

Fields with a resolver are also inherited from regular Strawberry types and
interfaces, when they're methods decorated with `@strawberry.field` (see
[`@strawberry.pydantic.interface`](#strawberrypydanticinterface)).

<Note>

Fields like `label: str = strawberry.field(resolver=get_label)` can't be
inherited from a regular Strawberry type or interface: Pydantic sees their
annotation and makes them fields of the model, so they raise an
[`UnsupportedInheritedFieldError`](../errors/unsupported-inherited-field.md).
Declare them as methods with `@strawberry.field` instead.

</Note>

### Scalars

Fields can use Strawberry's scalars, such as `strawberry.ID` and `JSON`, and
[custom scalars](../types/scalars.md), the same way as `@strawberry.type`.
Pydantic types that only add validation to a scalar, like `EmailStr`, `HttpUrl`,
`PositiveInt`, `AwareDatetime` or `PastDate`, use the scalar they validate, so
`scalar_map` entries for `datetime` also apply to `AwareDatetime` fields, and
`strawberry.field(graphql_type=...)` changes the scalar of a field. Pydantic's
URL and DSN types (including your own subclasses of them), `NameEmail` and the
`IPvAny*` types are strings, which Pydantic validates on inputs.

An exact `scalar_map` entry, such as one for `EmailStr`, takes precedence over
these automatic mappings. Mappings are resolved separately for each schema;
building one schema does not change another schema using the same models. An
undecorated Pydantic model can also be registered as a custom scalar. Models not
registered as scalars still need a Strawberry decorator; that check runs during
schema construction, once the scalar map is available.

```python
from typing import NewType

from pydantic import BaseModel

import strawberry
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

Money = NewType("Money", str)


@strawberry.pydantic.type
class Product(BaseModel):
    id: strawberry.ID
    price: Money
    metadata: JSON


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        scalar_map={
            Money: strawberry.scalar(name="Money", serialize=str, parse_value=str)
        }
    ),
)
```

Types that GraphQL has no scalar for, like `dict`, `Any`, `set` or `bytes`, need
a GraphQL type too, for example `JSON` or a custom scalar:

```python
from typing import Annotated, Any

from strawberry.scalars import JSON


@strawberry.pydantic.type
class Settings(BaseModel):
    values: Annotated[dict[str, Any], strawberry.field(graphql_type=JSON)]
```

`Literal` types aren't supported yet. Expose them with the type of their values,
Pydantic still validates the values sent by clients:

```python
from typing import Annotated, Literal


@strawberry.pydantic.input
class PostInput(BaseModel):
    status: Annotated[Literal["draft", "published"], strawberry.field(graphql_type=str)]
```

As with `@strawberry.type`, a `NewType` must be registered as a scalar to be
used in the schema. To expose it as its base type instead, set the GraphQL type
of the field:

```python
from typing import Annotated, NewType

UserId = NewType("UserId", int)


@strawberry.pydantic.type
class User(BaseModel):
    id: Annotated[UserId, strawberry.field(graphql_type=int)]
```

For [file uploads](../guides/file-upload.md), Pydantic validates the file
objects provided by your integration. A bare `Upload` annotation validates as
`bytes`, so file objects need a custom Pydantic validator, or an annotation
using the actual file type with `Upload` as its GraphQL type:

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict
from starlette.datastructures import UploadFile

import strawberry
from strawberry.file_uploads import Upload


@strawberry.pydantic.input
class CreatePostInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    image: Annotated[UploadFile, strawberry.field(graphql_type=Upload)]
```

## Advanced Usage

### Self-Referencing Models

Models can reference themselves, and models defined in the same module can
reference each other:

```python
@strawberry.pydantic.type
class Category(BaseModel):
    name: str
    children: list["Category"] = []
```

When the annotation of a field is a string that uses a model defined later, for
example with `from __future__ import annotations`, Pydantic only reads its
`Annotated` options once that model is defined. Until then, the field can't use
options like `strawberry.field()` or `Field(exclude=True)`: decorating the model
raises an
[`UnresolvedAnnotatedFieldError`](../errors/unresolved-annotated-field.md),
whose page shows the workarounds: defining the referenced model first, quoting
only the type, like `Annotated[list["Post"], strawberry.field(...)]`, in a
module without `from __future__ import annotations`, or decorating the model
after calling `model_rebuild()`.

Decoration captures the GraphQL fields and their mappings. Calling
`model_rebuild()` afterward only rebuilds Pydantic's model; it does not refresh
those captured fields or mappings. If unresolved references affect field
metadata or the mapping to GraphQL types (for example, a Pydantic-specific
scalar), resolve them and call `model_rebuild()` **before** decorating.

Models from other modules can be referenced with
[`strawberry.lazy()`](../types/lazy.md), for example when two modules import
each other:

```python
# authors.py
from typing import TYPE_CHECKING, Annotated

import strawberry
from pydantic import BaseModel

if TYPE_CHECKING:
    from .books import Book


@strawberry.pydantic.type
class Author(BaseModel):
    name: str
    books: list[Annotated["Book", strawberry.lazy(".books")]] = []
```

```python
# books.py
import strawberry
from pydantic import BaseModel

from .authors import Author


@strawberry.pydantic.type
class Book(BaseModel):
    title: str
    author: Author | None = None


# like any Pydantic model that uses a type defined later
Author.model_rebuild()
```

<Note>

Models in different modules that import each other without `strawberry.lazy()`
(using a `TYPE_CHECKING` import and `model_rebuild()` only) are not supported
yet. Use `strawberry.lazy()` for the types imported with `TYPE_CHECKING`, or
define the models in the same module.

</Note>

### Generic Models

Generic models work like generic Strawberry types: decorate the generic model,
and use its parametrizations, like `Page[User]`, as types. Each one is a GraphQL
type named after its arguments:

```python
from typing import Generic, TypeVar

T = TypeVar("T")


@strawberry.pydantic.type
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


@strawberry.pydantic.type
class User(BaseModel):
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> Page[User]:
        return Page[User](items=[User(name="Ada")], total=1)
```

```graphql
type UserPage {
  items: [User!]!
  total: Int!
}
```

Generic inputs and interfaces work the same way, and resolvers can also return
instances of the generic model itself, like `Page(items=[...], total=1)`. To
give a parametrization a name of your own, decorate a subclass of it:

```python
@strawberry.pydantic.type
class Users(Page[User]):
    pass
```

Generic models that reference their own parametrizations, like a `Tree[T]` with
`children: list[Tree[T]]`, aren't supported yet.

### Validation

Pydantic validation is automatically applied to input types. Strawberry supports
all Pydantic v2 validation features including field validators, model
validators, and functional validators.

#### Field Validators

```python
from pydantic import field_validator


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    age: int

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be non-negative")
        return v
```

#### Model Validators

Cross-field validation using `@model_validator`:

```python
from pydantic import model_validator


@strawberry.pydantic.input
class DateRangeInput(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> "DateRangeInput":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self
```

#### Functional Validators

Reusable validation with `Annotated` types:

```python
from typing import Annotated
from pydantic import AfterValidator


def validate_email(v: str) -> str:
    if "@" not in v:
        raise ValueError("Invalid email")
    return v.lower()


Email = Annotated[str, AfterValidator(validate_email)]


@strawberry.pydantic.input
class UserInput(BaseModel):
    email: Email  # Validator runs during GraphQL input processing
```

#### Nested Inputs

Pydantic inputs nested inside other Pydantic inputs are validated together with
the outermost one, so all the errors are reported at once, with their full
location:

```python
@strawberry.pydantic.input
class ItemInput(BaseModel):
    quantity: int = Field(gt=0)


@strawberry.pydantic.input
class OrderInput(BaseModel):
    items: list[ItemInput]
```

Sending `items: [{quantity: 0}, {quantity: 1}, {quantity: -1}]` reports two
errors, with locations `["input", "items", "0", "quantity"]` and
`["input", "items", "2", "quantity"]` for an argument named `input`. Every
segment is a string, including list indexes, matching the `[String!]!` GraphQL
field. Validators with `mode="before"` receive nested inputs as data, not as
model instances.

Strawberry converts GraphQL field names and scalar values, and transports lists
as tuples for tuple fields. Pydantic owns nested validation: Strawberry does not
prevalidate nested models for `PlainValidator`, `SkipValidation` or
`InstanceOf`. Their normal Pydantic behavior applies to the transported data; in
particular, `InstanceOf` does not turn a nested input object into a model
instance.

Collecting nested errors together only applies inside a Pydantic input: each
item of an argument like `inputs: list[ItemInput]` is validated on its own, and
the errors of the first invalid item are returned. Wrap the list in a Pydantic
input to report the errors of all the items.

A Pydantic input nested inside a regular `@strawberry.input` is validated on its
own, and overriding `model_validate` only affects the outermost input, so prefer
`@model_validator(mode="before")` to transform the input data.

#### Validation Errors

When a Pydantic input is invalid, the GraphQL response contains an error with
each problem in its `validationErrors` extension. For example, with this input:

```python
@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str = Field(min_length=2)
```

a `createUser` mutation that receives an invalid `input`:

```graphql
mutation {
  createUser(input: { name: "J" }) {
    name
  }
}
```

returns:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Invalid input: input.name: String should have at least 2 characters",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["createUser"],
      "extensions": {
        "validationErrors": [
          {
            "location": ["input", "name"],
            "message": "String should have at least 2 characters",
            "type": "string_too_short"
          }
        ]
      }
    }
  ]
}
```

`location` is a list of strings using the GraphQL names the client sent,
starting with the argument; list indexes are strings too. This applies to both
typed results and the `validationErrors` extension. The dotted path in the
top-level error message is only a human-readable summary. `type` is the
[Pydantic error type](https://docs.pydantic.dev/latest/errors/validation_errors/).
Errors raised by model validators are located at the model they validate: the
`DateRangeInput` check above is reported at `["range"]` for an argument named
`range`, or at `["input", "dates"]` when it's the `dates` field of an `input`
argument. The `input` property Pydantic attaches to errors is omitted, and
chaining to the original Pydantic exception is suppressed. Messages are
preserved from Pydantic, except that a validator's `ValueError` uses the
original exception message without Pydantic's generated `"Value error, "`
prefix. For example, `raise ValueError("An ISBN has 13 digits")` produces
`"An ISBN has 13 digits"`, with type `"value_error"`. Custom Pydantic error
messages and built-in constraint messages are unchanged. This applies to both
typed results and GraphQL errors.

Messages may contain submitted values, even for built-in errors. Removing the
prefix is not redaction; avoid sensitive values in custom validator messages and
review the errors your API exposes.

The error is raised as `strawberry.pydantic.InputValidationError`, a
[`StrawberryInputCoercionError`](../guides/errors.md#strawberry-input-coercion-errors),
so it can be told apart from server errors. Its `issues` attribute is the list
of `ValidationIssue`s, each with the `location`, `message` and `type` of a
problem, which you can use for example in your own
[exception handler](../guides/errors.md#mapping-expected-exceptions-to-union-results).
Each argument is validated on its own, so when several arguments are invalid,
the errors of the first one are returned.

To return validation errors as data instead, add
`strawberry.pydantic.ValidationError` to the field's return type and register
`PydanticValidationErrorHandler` on the schema:

```python
from pydantic import BaseModel, Field

import strawberry
from strawberry.pydantic import PydanticValidationErrorHandler, ValidationError


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str = Field(min_length=2)


@strawberry.pydantic.type
class User(BaseModel):
    name: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User | ValidationError:
        return User(name=input.name)


@strawberry.type
class Query:
    ok: bool = True


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    exception_handlers=[PydanticValidationErrorHandler()],
)
```

```graphql
mutation {
  createUser(input: { name: "J" }) {
    ... on User {
      name
    }
    ... on ValidationError {
      issues {
        location
        message
        type
      }
    }
  }
}
```

Only `InputValidationError`s are returned as `ValidationError`: Pydantic errors
raised by your resolvers are reported as normal errors, and exception handlers
for `pydantic.ValidationError` only receive those (see
[TypeAdapter and RootModel](#typeadapter-and-rootmodel) to report them like
invalid inputs). Like other exception handlers, it doesn't apply to
subscriptions and list fields, which return the GraphQL error instead.

### Model Config

Pydantic's `model_config` settings are respected during validation, for example
`str_strip_whitespace` or `str_to_lower`:

```python
from pydantic import ConfigDict


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str  # "  Ada " is validated as "Ada"
```

GraphQL already checks the types of the values, and doesn't allow unknown
fields, before Pydantic validates the input, so settings like `strict=True` and
`extra="forbid"` mostly matter when the model is also used outside of GraphQL.
For tuple fields, Strawberry converts GraphQL lists to Python tuples before
Pydantic validation, including in strict mode. Pydantic still validates their
items and constraints.

### Field Directives and Customization

You can use `strawberry.field()` with `Annotated` types to add GraphQL-specific
features like directives, permissions, and deprecation to individual Pydantic
model fields:

```python
from typing import Annotated
from pydantic import BaseModel, Field
import strawberry
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Sensitive:
    reason: str


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Range:
    min: int
    max: int


@strawberry.pydantic.type
class User(BaseModel):
    # Regular field - uses Pydantic description
    name: Annotated[str, Field(description="The user's full name")]

    # Field with directive
    email: Annotated[str, strawberry.field(directives=[Sensitive(reason="PII")])]

    # Field with multiple directives and Pydantic features
    age: Annotated[
        int,
        Field(description="User's age"),
        strawberry.field(directives=[Range(min=0, max=150)]),
    ]

    # Field with permissions
    phone: Annotated[
        str,
        strawberry.field(
            permission_classes=[IsAuthenticated],
            directives=[Sensitive(reason="Contact Info")],
        ),
    ]

    # Deprecated field
    old_id: Annotated[int, strawberry.field(deprecation_reason="Use 'id' instead")]
```

#### Field Customization Options

When using `strawberry.field()` with Pydantic models, you can specify:

- **`directives`**: List of GraphQL directives to apply to the field
- **`permission_classes`**: List of permission classes for field-level
  authorization
- **`deprecation_reason`**: Mark a field as deprecated with a reason
- **`description`**: Override the Pydantic field description for GraphQL
- **`name`**: Set the GraphQL field name
- **`graphql_type`**: Override the GraphQL type of the field

`strawberry.field()` must be used inside `Annotated`. Assigning it as the
default value (`email: str = strawberry.field(...)`) raises an error, because
Pydantic would keep only its default and discard the rest of its configuration.

Defaults belong to Pydantic: use `count: int = 7` or
`pydantic.Field(default_factory=...)`. A `default` or `default_factory` inside
`Annotated[..., strawberry.field(...)]` raises a `TypeError` rather than being
silently ignored; Pydantic does not use that metadata to construct the model.

Customizations declared on a base model or on an interface are inherited by its
subclasses and implementations.

#### Input Types with Directives

Field directives work with input types too:

```python
from strawberry.schema_directive import Location


@strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
class Validate:
    pattern: str


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    email: Annotated[
        str, strawberry.field(directives=[Validate(pattern=r"^[^@]+@[^@]+\.[^@]+")])
    ]
```

### TypeAdapter and RootModel

A `RootModel` holds a single value instead of fields, so it can't be decorated
as an object type or an input. To use one as a field, register a custom scalar
for it in `scalar_map`. Pydantic's `TypeAdapter` and `RootModel` can be used in
resolvers for additional validation:

```python
from pydantic import TypeAdapter, RootModel, Field
from typing import Annotated

# Using TypeAdapter for scalar validation
PositiveInt = Annotated[int, Field(gt=0)]
positive_adapter = TypeAdapter(PositiveInt)


@strawberry.type
class Query:
    @strawberry.field
    def validate_positive(self, value: int) -> int:
        return positive_adapter.validate_python(value)


# Using RootModel for list validation
class BoundedList(RootModel[Annotated[list[int], Field(min_length=1, max_length=5)]]):
    pass


@strawberry.type
class Mutation:
    @strawberry.mutation
    def process_items(self, items: list[int]) -> int:
        validated = BoundedList.model_validate(items)
        return sum(validated.root)
```

These errors aren't input errors: a Pydantic `ValidationError` raised by a
resolver is reported as a regular GraphQL error, whose message is Pydantic's,
which includes the input values, like
`Input should be greater than 0 [type=greater_than, input_value=-3, input_type=int]`.
The [`PydanticErrorExtension`](../extensions/pydantic_error_extension.md) adds
these errors to the response in a `validation_errors` extension, with a
different shape than invalid inputs: a `field` and a `message` for each error.

### Relay

Pydantic types can implement [`relay.Node`](../guides/relay.md) like regular
Strawberry types: annotate the field that holds the ID with `relay.NodeID`,
which Pydantic validates like any other field and the schema leaves out, as
`relay.Node` exposes it as a global ID, and resolve the nodes with a
`resolve_nodes` class method:

```python
from collections.abc import Iterable

from strawberry import relay


@strawberry.pydantic.type
class Fruit(BaseModel, relay.Node):
    id: relay.NodeID[int]
    name: str

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
        required: bool = False,
    ) -> list["Fruit | None"]:
        return [get_fruit(int(node_id)) for node_id in node_ids]


@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(relay.ListConnection[Fruit])
    def fruits(self) -> list[Fruit]:
        return get_fruits()
```

Like other regular Strawberry interfaces, `relay.Node` comes after `BaseModel`
in the bases. Pydantic types that don't implement `relay.Node` can be the nodes
of connections too.

### Federation

Pydantic types can be [federation](../guides/federation.md) entities. There are
no `strawberry.federation` versions of the decorators, so pass the federation
directives, like `Key`, with `directives`:

```python
from pydantic import BaseModel

import strawberry
from strawberry.federation.schema_directives import Key


@strawberry.pydantic.type(directives=[Key(fields="id")])
class Product(BaseModel):
    id: strawberry.ID

    @strawberry.pydantic.field
    def reviews(self) -> list["Review"]:
        return get_reviews(product_id=self.id)


@strawberry.pydantic.type(directives=[Key(fields="id")])
class Review(BaseModel):
    id: strawberry.ID
    body: str

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Review":
        return get_review(id)


schema = strawberry.federation.Schema(query=Query, types=[Product])
```

Like other entities, they are resolved with their `resolve_reference` class
method. Entities without one, like `Product`, are built by validating the
representation sent by the router with Pydantic. A router only sends the key
fields of an entity, and the fields that `@requires` asks for, so the model's
other non-null fields need a default (nullable ones are `None` when they're
missing). An invalid representation is reported like an invalid input: the
entity is `null`, with an error that has a `validationErrors` extension, which
reports a missing field as `Field required`.

<Note>

The `ValidationError` and `ValidationIssue` types aren't `@shareable` yet, so
two subgraphs that both use them don't compose: composition fails with
`INVALID_FIELD_SHARING` errors.

</Note>

## Complete Example

```python
from pydantic import BaseModel, Field, field_validator

import strawberry
from strawberry.pydantic import PydanticValidationErrorHandler, ValidationError


@strawberry.pydantic.type
class User(BaseModel):
    id: strawberry.ID
    name: str = Field(description="The user's full name")
    email: str
    tags: list[str] = Field(default_factory=list)

    @strawberry.pydantic.field
    def initials(self) -> str:
        return "".join(part[0] for part in self.name.split())


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str = Field(min_length=1)
    email: str
    tags: list[str] = []

    @field_validator("email")
    @classmethod
    def check_email(cls, email: str) -> str:
        if "@" not in email:
            raise ValueError("Invalid email")

        return email


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID) -> User | None:
        return User(id=id, name="Ada Lovelace", email="ada@example.com")


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User | ValidationError:
        return User(id=strawberry.ID("1"), **input.model_dump())


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    exception_handlers=[PydanticValidationErrorHandler()],
)
```

---

# Experimental Pydantic Support

The experimental integration, `strawberry.experimental.pydantic`, creates a
separate Strawberry class for each Pydantic model, and also supports Pydantic v1
models. It's still supported, next to `strawberry.pydantic`.

## Moving from the experimental integration

To move a model from the experimental integration to `strawberry.pydantic`, keep
in mind that the same model can give a different schema, which can break
existing clients:

- Pydantic aliases were the GraphQL names of the fields by default, now the
  Python names are, on types and inputs. An alias like `userName` for
  `user_name` gives the same name, but one like `login` doesn't: keep it as the
  GraphQL name with
  `Annotated[str, Field(alias="login"), strawberry.field(name="login")]`.
- Fields excluded with `Field(exclude=True)` are no longer exposed on output
  types.
- Computed fields are included in output types, unless `include_computed=False`
  is passed to the decorator.
- Fields deprecated with `Field(deprecated=...)` are deprecated in GraphQL with
  `@deprecated`.

The two integrations can't use each other's types: a field of a
`strawberry.pydantic` type can't use a model that only has an experimental type,
and the other way around. Move models that reference each other together, or
give a model a `strawberry.pydantic` type too while its experimental type is
still used, with a different name if both are in the schema:

```python
strawberry.pydantic.type(AddressModel, name="NewAddress")
```

## Experimental Usage

The experimental integration uses a separate Strawberry class for each model:

```python
from strawberry.experimental.pydantic import type as pydantic_type


class UserModel(BaseModel):
    id: int
    name: str
    signup_ts: Optional[datetime] = None
    friends: List[int] = []


@pydantic_type(model=UserModel)
class UserType:
    id: strawberry.auto
    name: strawberry.auto
    friends: strawberry.auto


# Or include all fields
@pydantic_type(model=UserModel, all_fields=True)
class UserType:
    pass
```

### Input types

Input types are similar to types; we can create one by using the
`strawberry.experimental.pydantic.input` decorator:

```python
import strawberry

from .models import User


@strawberry.experimental.pydantic.input(model=User)
class UserInput:
    id: strawberry.auto
    name: strawberry.auto
    friends: strawberry.auto
```

## Interface types

Interface types are similar to normal types; we can create one by using the
`strawberry.experimental.pydantic.interface` decorator:

```python
import strawberry
from pydantic import BaseModel
from typing import List


# pydantic types
class User(BaseModel):
    id: int
    name: str


class NormalUser(User):
    friends: List[int] = []


class AdminUser(User):
    role: int


# strawberry types
@strawberry.experimental.pydantic.interface(model=User)
class UserType:
    id: strawberry.auto
    name: strawberry.auto


@strawberry.experimental.pydantic.type(model=NormalUser)
class NormalUserType(UserType):  # note the base class
    friends: strawberry.auto


@strawberry.experimental.pydantic.type(model=AdminUser)
class AdminUserType(UserType):
    role: strawberry.auto
```

## Error Types

In addition to object types and input types, Strawberry allows you to create
"error types". You can use these error types to have a typed representation of
Pydantic errors in GraphQL. Let's see an example:

<CodeGrid>

```python
from pydantic import BaseModel, constr
import strawberry


class User(BaseModel):
    id: int
    name: constr(min_length=2)
    signup_ts: Optional[datetime] = None
    friends: List[int] = []


@strawberry.experimental.pydantic.error_type(model=User)
class UserError:
    id: strawberry.auto
    name: strawberry.auto
    friends: strawberry.auto
```

```graphql
type UserError {
  id: [String!]
  name: [String!]
  friends: [[String!]]
}
```

</CodeGrid>

where each field will hold a list of error messages

## Extending types

You can use the usual Strawberry syntax to add additional new fields to the
GraphQL type that aren't defined in the pydantic model

<CodeGrid>

```python
import strawberry
from pydantic import BaseModel

from .models import User


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.type(model=User)
class User:
    id: strawberry.auto
    name: strawberry.auto
    age: int
```

```graphql
type User {
  age: Int!
  id: Int!
  name: String!
}
```

</CodeGrid>

## Converting types

The generated types won't run any pydantic validation. This is to prevent
confusion when extending types and also to be able to run validation exactly
where it is needed.

To convert a Pydantic instance to a Strawberry instance you can use
`from_pydantic` on the Strawberry type:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: strawberry.auto
    name: strawberry.auto


instance = User(id="123", name="Jake")

data = UserType.from_pydantic(instance)
```

If your Strawberry type includes additional fields that aren't defined in the
pydantic model, you will need to use the `extra` parameter of `from_pydantic` to
specify the values to assign to them.

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: strawberry.auto
    name: strawberry.auto
    age: int


instance = User(id="123", name="Jake")

data = UserType.from_pydantic(instance, extra={"age": 10})
```

The data dictionary structure follows the structure of your data -- if you have
a list of `User`, you should send an `extra` that is the list of `User` with the
missing data (in this case, `age`).

You don't need to send all fields; data from the model is used first and then
the `extra` parameter is used to fill in any additional missing data.

To convert a Strawberry instance to a pydantic instance and trigger validation,
you can use `to_pydantic` on the Strawberry instance:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.input(model=User)
class UserInput:
    id: strawberry.auto
    name: strawberry.auto


input_data = UserInput(id="abc", name="Jake")

# this will run pydantic's validation, which raises a ValidationError here, as
# "abc" isn't an integer
instance = input_data.to_pydantic()
```

## Constrained types

Strawberry supports
[pydantic constrained types](https://pydantic-docs.helpmanual.io/usage/types/#constrained-types).
Note that constraint is not enforced in the graphql type. Thus, we recommend
always working on the pydantic type such that the validation is enforced.

<CodeGrid>

```python
from pydantic import BaseModel, conlist
import strawberry


class Example(BaseModel):
    friends: conlist(str, min_items=1)


@strawberry.experimental.pydantic.input(model=Example, all_fields=True)
class ExampleGQL: ...


@strawberry.type
class Query:
    @strawberry.field()
    def test(self, example: ExampleGQL) -> None:
        # friends may be an empty list here
        print(example.friends)
        # calling to_pydantic() runs the validation and raises
        # an error if friends is empty
        print(example.to_pydantic().friends)


schema = strawberry.Schema(query=Query)
```

```graphql
input ExampleGQL {
  friends: [String!]!
}

type Query {
  test(example: ExampleGQL!): Void
}
```

</CodeGrid>

## Classes with `__get_validators__`

Pydantic BaseModels may define a custom type with
[`__get_validators__`](https://pydantic-docs.helpmanual.io/usage/types/#classes-with-__get_validators__)
logic. You will need to add a scalar type and add the mapping to the
`scalar_overrides` argument in the Schema class.

```python
import strawberry
from pydantic import BaseModel


class MyCustomType:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return MyCustomType()


class Example(BaseModel):
    custom: MyCustomType


@strawberry.experimental.pydantic.type(model=Example, all_fields=True)
class ExampleGQL: ...


MyScalarType = strawberry.scalar(
    MyCustomType,
    # or another function describing how to represent MyCustomType in the response
    serialize=str,
    parse_value=lambda v: MyCustomType(),
)


@strawberry.type
class Query:
    @strawberry.field()
    def test(self) -> ExampleGQL:
        return Example(custom=MyCustomType())


# Tells strawberry to convert MyCustomType into MyScalarType
schema = strawberry.Schema(query=Query, scalar_overrides={MyCustomType: MyScalarType})
```

## Custom Conversion Logic

Sometimes you might not want to translate your Pydantic model into Strawberry
using the logic provided in the library. Sometimes types in Pydantic are
unrepresentable in GraphQL (such as unions of scalar values) or structural
changes are needed before the data is exposed in the schema. In these cases,
there are two methods you can use to control the conversion logic more directly.

First, you can use a different type annotation in your Strawberry model for a
field type instead of using `strawberry.auto` to choose an equivalent type. This
allows you to do things like converting values to custom scalar types or
converting between basic types. Strawberry will call the constructor of the new
type annotation with the field value as input, so this only works when
conversion is possible through a constructor.

```python
import base64
import strawberry
from pydantic import BaseModel
from typing import Union, NewType


class User(BaseModel):
    id: Union[int, str]  # Not representable in GraphQL
    hash: bytes


Base64 = strawberry.scalar(
    NewType("Base64", bytes),
    serialize=lambda v: base64.b64encode(v).decode("utf-8"),
    parse_value=lambda v: base64.b64decode(v.encode("utf-8")),
)


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: str  # Serialize int values to strings
    hash: Base64  # Use a custom scalar to serialize values


@strawberry.type
class Query:
    @strawberry.field
    def test() -> UserType:
        return UserType.from_pydantic(User(id=123, hash=b"abcd"))


schema = strawberry.Schema(query=Query)

print(schema.execute_sync("query { test { id, hash } }").data)
# {"test": {"id": "123", "hash": "YWJjZA=="}}
```

The other, more comprehensive, method for modifying the conversion logic is to
provide custom implementations of `from_pydantic` and `to_pydantic`. This allows
you full control over the conversion process and bypasses Strawberry's built in
conversion rules completely, while still registering the new type as a Pydantic
conversion type so it can be referenced in other models.

This is useful when you need to represent structures that are very different
from GraphQL standards, without changing the underlying Pydantic model. An
example would be a use case that uses a `dict` field to store some
semi-structured content, which is difficult to represent in GraphQL's strict
type system.

```python
import enum
import dataclasses
import strawberry
from pydantic import BaseModel
from typing import Any, Dict, Optional


class ContentType(enum.Enum):
    NAME = "name"
    DESCRIPTION = "description"


class User(BaseModel):
    id: str
    content: Dict[ContentType, str]


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: strawberry.auto
    # Flatten the content dict into specific fields in the query
    content_name: Optional[str] = None
    content_description: Optional[str] = None

    @staticmethod
    def from_pydantic(instance: User, extra: Dict[str, Any] = None) -> "UserType":
        data = instance.dict()
        content = data.pop("content")
        data.update({f"content_{k.value}": v for k, v in content.items()})
        return UserType(**data)

    def to_pydantic(self) -> User:
        data = dataclasses.asdict(self)

        # Pull out the content_* fields into a dict
        content = {}
        for enum_member in ContentType:
            key = f"content_{enum_member.value}"
            if data.get(key) is not None:
                content[enum_member.value] = data.pop(key)
        return User(content=content, **data)


user = User(id="abc", content={ContentType.NAME: "Bob"})
print(UserType.from_pydantic(user))
# UserType(content_name='Bob', content_description=None, id='abc')

user_type = UserType(id="abc", content_name="Bob", content_description=None)
print(user_type.to_pydantic())
# id='abc' content={<ContentType.NAME: 'name'>: 'Bob'}
```
