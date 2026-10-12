---
title: Pydantic support
experimental: true
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
exactly one field:

```python
@strawberry.pydantic.input(one_of=True)
class UserBy(BaseModel):
    id: strawberry.ID | None = None
    email: str | None = None
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
[schema directives](../types/schema-directives.md) for the type.

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
in the [experimental integration](#experimental-pydantic-support)). Use
`strawberry.field(name=...)` to rename a field:

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

### Deprecated Fields

Fields deprecated with Pydantic's `Field(deprecated=...)` are deprecated in the
GraphQL schema too. Pydantic still emits its `DeprecationWarning` when the field
is read, including when it's resolved.

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

### Default Values and Partial Updates

Input fields with a default can be omitted by clients. Defaults that are
constants of the field's type, like `20` for an `int` field or an enum member
for an enum field, are shown in the schema:

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
  tag: String
}
```

Other defaults, like `None`, default factories, model instances or values that
Pydantic converts to the field's type, are applied by Pydantic and are not shown
in the schema, so the field becomes nullable. Pydantic validates an explicit
`null` like any other value.

A nullable field without a default, like `nickname: str | None`, is optional for
clients too, as GraphQL requires for nullable input fields. When a client leaves
it out, Pydantic gets `None` for it, as if the client had sent `null`: the field
is part of `model_fields_set`, and validators see `None`. Give the field a
default, like `= None`, to tell the two apart, for example for partial updates.

Fields the client omits whose default is not shown in the schema are not part of
`model_fields_set`, which makes partial updates work as usual with Pydantic:

```python
@strawberry.pydantic.input
class UpdateUserInput(BaseModel):
    name: str | None = None
    bio: str | None = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, id: strawberry.ID, input: UpdateUserInput) -> User:
        user = get_user(id)

        # only the fields sent by the client, an explicit `null` included
        for field, value in input.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        return user
```

Defaults shown in the schema are filled in by GraphQL in the inputs clients
send, so they are always part of their `model_fields_set`, and Pydantic
validates them like values sent by the client.

When a model is the default of an argument, only the fields that were set on it
are part of the default shown in the schema, and the model the resolver gets
when the client omits the argument has the same `model_fields_set`. For example,
the default of `input: UpdateUserInput = UpdateUserInput(name="Ada")` is
`{ name: "Ada" }`, so a partial update doesn't overwrite the other fields with
`None`. Like the values sent by clients, the default is validated again for
every request that uses it.

`strawberry.Maybe` can't be used in Pydantic inputs (Pydantic raises an error
for it when the model is defined), give the field a default and use
`model_fields_set` to tell omitted fields apart from explicit `null` values
instead.

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
from the model's attributes, not from `model_dump()`, so Pydantic's serializers
(`field_serializer`, `PlainSerializer`, `WrapSerializer` and
`model_serializer`), serialization aliases and `Field(exclude_if=...)` are not
applied. To hide a value, use `strawberry.Private` or `Field(exclude=True)`.

### Scalars

Fields can use Strawberry's scalars, such as `strawberry.ID` and `JSON`, and
[custom scalars](../types/scalars.md), the same way as `@strawberry.type`:

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

The same applies to [file uploads](../guides/file-upload.md): uploaded files are
the file objects of your integration, which Pydantic can't validate as `Upload`,
so input fields typed as `Upload` raise an error. Annotate the field with the
file type and use `Upload` as its GraphQL type instead:

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

### Generic Models

To use a generic model, decorate a subclass of it with concrete types:

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


@strawberry.pydantic.type
class User(BaseModel):
    name: str


@strawberry.pydantic.type
class UserPage(Page[User]):
    pass


@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> UserPage:
        return UserPage(items=[User(name="Ada")], total=1)
```

Using the parametrized model directly, like `-> Page[User]`, isn't supported
yet.

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
errors, at `input.items.0.quantity` and `input.items.2.quantity` for an argument
named `input`. Validators with `mode="before"` receive nested inputs as data,
not as model instances.

This only applies to inputs nested in a Pydantic input: each item of an argument
like `inputs: list[ItemInput]` is validated on its own, and the errors of the
first invalid item are returned. Wrap the list in a Pydantic input to report the
errors of all the items.

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

`location` uses the GraphQL names the client sent, starting with the argument,
and `type` is the
[Pydantic error type](https://docs.pydantic.dev/latest/errors/validation_errors/).
Errors raised by model validators are located at the model they validate: the
`DateRangeInput` check above is reported at `["range"]` for an argument named
`range`, or at `["input", "dates"]` when it's the `dates` field of an `input`
argument. The values Pydantic attaches to its errors are not included, but
messages come from Pydantic and from your validators, so avoid putting sensitive
values in your validators' messages.

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
One exception: GraphQL lists are sent to Pydantic as Python lists, which strict
mode doesn't accept for `tuple` fields.

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

Pydantic's `TypeAdapter` and `RootModel` can be used in resolvers for additional
validation:

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

---

# Experimental Pydantic Support

Strawberry comes with support for
[Pydantic](https://pydantic-docs.helpmanual.io/). This allows for the creation
of Strawberry types from pydantic models without having to write code twice.

Here's a basic example of how this works, let's say we have a pydantic Model for
a user, like this:

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    signup_ts: Optional[datetime] = None
    friends: List[int] = []
```

We can create a Strawberry type by using the
`strawberry.experimental.pydantic.type` decorator:

```python
import strawberry

from .models import User


@strawberry.experimental.pydantic.type(model=User)
class UserType:
    id: strawberry.auto
    name: strawberry.auto
    friends: strawberry.auto
```

The `strawberry.experimental.pydantic.type` decorator accepts a Pydantic model
and wraps a class that contains dataclass style fields with `strawberry.auto` as
the type annotation. The fields marked with `strawberry.auto` will inherit their
types from the Pydantic model.

If you want to include all of the fields from your Pydantic model, you can
instead pass `all_fields=True` to the decorator.

-> **Note** Care should be taken to avoid accidentally exposing fields that ->
weren't meant to be exposed on an API using this feature.

```python
import strawberry

from .models import User


@strawberry.experimental.pydantic.type(model=User, all_fields=True)
class UserType:
    pass
```

By default, computed fields are excluded. To also include all computed fields
pass `include_computed=True` to the decorator.

```python
import strawberry

from .models import User


@strawberry.experimental.pydantic.type(
    model=User, all_fields=True, include_computed=True
)
class UserType:
    pass
```

## Input types

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
  id: Int!
  name: String!
  age: Int!
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

# this will run pydantic's validation
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
# UserType(id='abc', content_name='Bob', content_description=None)

user_type = UserType(id="abc", content_name="Bob", content_description=None)
print(user_type.to_pydantic())
# id='abc' content={<ContentType.NAME: 'name'>: 'Bob'}
```
