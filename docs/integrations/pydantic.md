---
title: Pydantic support
---

# Pydantic support

Strawberry provides first-class support for [Pydantic](https://pydantic.dev/)
models, allowing you to directly decorate your Pydantic `BaseModel` classes to
create GraphQL types without writing code twice.

## Installation

```bash
pip install strawberry-graphql[pydantic]
```

`strawberry.pydantic` requires Pydantic 2.11 or newer. Pydantic v1 models are
only supported by the
[experimental integration](#experimental-pydantic-support-deprecated).

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

### `@strawberry.pydantic.input`

Creates a GraphQL input type from a Pydantic model:

```python
@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    age: int
    email: str


@strawberry.type
class Mutation:
    @strawberry.field
    def create_user(self, input: CreateUserInput) -> User:
        return User(name=input.name, age=input.age, email=input.email)
```

### `@strawberry.pydantic.interface`

Creates a GraphQL interface from a Pydantic model:

```python
@strawberry.pydantic.interface
class Node(BaseModel):
    id: str


@strawberry.pydantic.type
class User(BaseModel):
    id: str
    name: str
    # User implements Node interface
```

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
for example for a REST API, so they are not used in the GraphQL schema. Use
`strawberry.field(name=...)` to rename a field:

```python
from typing import Annotated

from pydantic import Field


@strawberry.pydantic.type
class User(BaseModel):
    user_name: str = Field(alias="user-name")  # userName in GraphQL
    age: Annotated[int, strawberry.field(name="yearsOld")]
```

This also applies to fields named after Python keywords, which are usually
aliased: `from_: date = Field(alias="from")` is called `from_` in GraphQL,
unless it is renamed with `Annotated[date, strawberry.field(name="from")]`.

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

### Deprecated Fields

Fields of output types deprecated with Pydantic's `Field(deprecated=...)` or
`computed_field(deprecated=...)` are deprecated in the GraphQL schema too.
Pydantic still emits its `DeprecationWarning` when the field is read, including
when it's resolved. Input fields are not deprecated in GraphQL, as GraphQL
doesn't allow deprecating required input fields.

```python
@strawberry.pydantic.type
class User(BaseModel):
    name: str
    full_name: str = Field(deprecated="Use name")
```

```graphql
type User {
  name: String!
  fullName: String! @deprecated(reason: "Use name")
}
```

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

Defaults shown in the schema are filled in by GraphQL, so they are always part
of `model_fields_set`, and Pydantic validates them like values sent by the
client.

`strawberry.Maybe` can't be used in Pydantic inputs, use `model_fields_set` to
tell omitted fields apart from explicit `null` values instead.

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

The private fields are still accessible in Python code for use in resolvers or
business logic:

```python
@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> User:
        user = User(id=1, name="John", password="secret", email="john@example.com")
        # Can access private field in Python
        if user.password:
            return user
        return None
```

Fields excluded from Pydantic's serialization with `Field(exclude=True)` are not
exposed on GraphQL types and interfaces either, so GraphQL never returns more
than `model_dump()` does:

```python
from pydantic import BaseModel, Field


@strawberry.pydantic.type
class ApiClient(BaseModel):
    name: str
    api_key: str = Field(exclude=True)  # Not exposed in GraphQL
```

Input types are not affected: clients can still send fields marked with
`exclude=True`.

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
other decorators, like `@staticmethod` or `@functools.cache`. They are inherited
from base models and from Pydantic interfaces, and the field is named after the
attribute, so `label = strawberry.pydantic.field(get_label)` adds a `label`
field.

Input types can't have fields with a resolver: the ones inherited from a base
model, for example one shared with an output type, are ignored. Use
`@strawberry.field` for regular Strawberry types.

If your model makes Pydantic ignore Strawberry fields, with
`model_config = ConfigDict(ignored_types=(StrawberryField,))`, you can use
`strawberry.field` too.

<Note>

A regular `@strawberry.interface` with fields that have a resolver can't be used
as a base of a Pydantic model, as Pydantic would treat these fields as model
fields. Use a `@strawberry.pydantic.interface` instead.

</Note>

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

### Nested Types

Pydantic models can contain other Pydantic models:

```python
@strawberry.pydantic.type
class Address(BaseModel):
    street: str
    city: str
    zipcode: str


@strawberry.pydantic.type
class User(BaseModel):
    name: str
    address: Address
```

Models can reference themselves, and models defined in the same module can
reference each other:

```python
@strawberry.pydantic.type
class Category(BaseModel):
    name: str
    children: list["Category"] = []
```

<Note>

Models in different modules that import each other (using a `TYPE_CHECKING`
import and `model_rebuild()`) are not supported yet. Define them in the same
module instead.

</Note>

### Lists and Collections

Lists of Pydantic models work seamlessly:

```python
from typing import List


@strawberry.pydantic.type
class User(BaseModel):
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def get_users(self) -> List[User]:
        return [User(name="John", age=30), User(name="Jane", age=25)]
```

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

A Pydantic input nested inside a regular `@strawberry.input` is validated on its
own, and overriding `model_validate` only affects the outermost input, so prefer
`@model_validator(mode="before")` to transform the input data.

#### Validation Context

Strawberry automatically passes GraphQL context to Pydantic validators, allowing
access to request information, user authentication, database sessions, etc:

```python
from pydantic import field_validator, ValidationInfo


@strawberry.pydantic.input
class CreatePostInput(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def check_permissions(cls, v: str, info: ValidationInfo) -> str:
        # Access GraphQL context passed during validation
        strawberry_info = info.context.get("info") if info.context else None
        if strawberry_info:
            user = strawberry_info.context.get("user")
            if user and not user.can_create_posts:
                raise ValueError("User cannot create posts")
        return v
```

#### Validation Errors

When a Pydantic input is invalid, the GraphQL response contains an error with
each problem in its `validationErrors` extension:

```graphql
mutation {
  createUser(input: { name: "J" }) {
    name
  }
}
```

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
The values Pydantic attaches to its errors are not included, but messages come
from Pydantic and from your validators, so avoid putting sensitive values in
your validators' messages.

The error is raised as `strawberry.pydantic.InputValidationError`, a
[`StrawberryInputCoercionError`](../guides/errors.md#strawberry-input-coercion-errors),
so it can be told apart from server errors. Each argument is validated on its
own, so when several arguments are invalid, the errors of the first one are
returned.

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

Only invalid inputs are returned as `ValidationError`: Pydantic errors raised by
your resolvers are reported as normal errors, and exception handlers for
`pydantic.ValidationError` only receive those. Like other exception handlers, it
doesn't apply to subscriptions and list fields, which return the GraphQL error
instead.

### Model Config

Pydantic's `model_config` settings are respected during validation:

```python
from pydantic import ConfigDict


@strawberry.pydantic.input
class StrictUserInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    age: int  # Will NOT accept "25" as string
    name: str
```

#### Per-Field Strict Mode

You can also enable strict mode on individual fields:

```python
from pydantic import Field


@strawberry.pydantic.input
class UserInput(BaseModel):
    age: int = Field(strict=True)  # Must be int, not "25"
    name: str  # Normal coercion allowed
```

### Field Directives and Customization

You can use `strawberry.field()` with `Annotated` types to add GraphQL-specific
features like directives, permissions, and deprecation to individual Pydantic
model fields:

```python
from typing import Annotated
from pydantic import BaseModel, Field
import strawberry


@strawberry.schema_directive(
    locations=[strawberry.schema_directive.Location.FIELD_DEFINITION]
)
class Sensitive:
    reason: str


@strawberry.schema_directive(
    locations=[strawberry.schema_directive.Location.FIELD_DEFINITION]
)
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
@strawberry.schema_directive(
    locations=[strawberry.schema_directive.Location.INPUT_FIELD_DEFINITION]
)
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

## Migration from Experimental

If you're using the experimental Pydantic integration, here's how to migrate:

### Before (Experimental)

```python
from strawberry.experimental.pydantic import type as pydantic_type


class UserModel(BaseModel):
    name: str
    age: int


@pydantic_type(UserModel, all_fields=True)
class User:
    pass
```

### After (First-class)

```python
@strawberry.pydantic.type
class User(BaseModel):
    name: str
    age: int
```

## Complete Example

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import strawberry


@strawberry.pydantic.type
class User(BaseModel):
    id: int
    name: str = Field(description="The user's full name")
    email: str
    age: int = Field(ge=0, description="The user's age in years")
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)


@strawberry.pydantic.input
class CreateUserInput(BaseModel):
    name: str
    email: str
    age: int
    tags: Optional[List[str]] = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Age must be non-negative")
        return v


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self, id: int) -> Optional[User]:
        return User(
            id=id,
            name="John Doe",
            email="john@example.com",
            age=30,
            tags=["developer", "python"],
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, input: CreateUserInput) -> User:
        return User(
            id=1,
            name=input.name,
            email=input.email,
            age=input.age,
            tags=input.tags or [],
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
```

---

# Experimental Pydantic Support (Deprecated)

The experimental Pydantic integration is deprecated in favor of the first-class
support above. The experimental integration will be removed in a future version.

## Experimental Usage

The experimental integration required creating separate wrapper classes:

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
