"""`strawberry.Maybe` fields of pydantic inputs."""

import inspect
from typing import Annotated, Any, get_origin

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic import PydanticValidationErrorHandler, ValidationError
from strawberry.pydantic.exceptions import MaybeFieldError

Name = Annotated[
    str, pydantic.StringConstraints(min_length=2), pydantic.AfterValidator(str.title)
]


@strawberry.pydantic.input
class AddressInput(pydantic.BaseModel):
    zip_code: str = pydantic.Field(pattern=r"^\d{5}$")


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: strawberry.Maybe[Name]
    phone: strawberry.Maybe[str | None]
    address: strawberry.Maybe[AddressInput | None]
    tags: strawberry.Maybe[list[str]] = None


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    hello: str = "world"


received: list[UpdateUserInput] = []


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> User | ValidationError:
        received.append(input)

        return User(name="Ada")


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    exception_handlers=[PydanticValidationErrorHandler()],
)

UPDATE_USER = """
    mutation UpdateUser($input: UpdateUserInput!) {
        updateUser(input: $input) {
            ... on User { name }
            ... on ValidationError { errors { location message type } }
        }
    }
"""


def update_user(input: dict[str, Any]) -> UpdateUserInput:
    """Run the mutation with `input` and return the model the resolver got."""
    received.clear()
    result = schema.execute_sync(UPDATE_USER, variable_values={"input": input})

    assert not result.errors
    assert result.data == {"updateUser": {"name": "Ada"}}
    (model,) = received

    return model


def test_schema():
    """`Maybe` fields are nullable, without a default, like on `@strawberry.input`."""
    assert str(schema) == snapshot('''\
input AddressInput {
  zipCode: String!
}

type Mutation {
  updateUser(input: UpdateUserInput!): UserValidationError!
}

type Query {
  hello: String!
}

input UpdateUserInput {
  name: String
  phone: String
  address: AddressInput
  tags: [String!]
}

type User {
  name: String!
}

union UserValidationError = User | ValidationError

"""The inputs failed validation."""
type ValidationError {
  """The problems with the input values."""
  errors: [ValidationErrorDetail!]!
}

"""A problem with an input value."""
type ValidationErrorDetail {
  """The argument, then field names and list indexes, all as strings."""
  location: [String!]!

  """The reason the value is invalid."""
  message: String!

  """The Pydantic error type, like `string_too_short`."""
  type: String!
}\
''')


def test_fields_left_out_are_none():
    model = update_user({})

    assert model.name is None
    assert model.phone is None
    assert model.address is None
    assert model.tags is None
    assert model.model_fields_set == set()
    assert model.model_dump(exclude_unset=True) == {}


def test_values_are_validated_and_wrapped_in_some():
    model = update_user(
        {
            "name": "ada",
            "phone": "555",
            "address": {"zipCode": "12345"},
            "tags": ["admin"],
        }
    )

    assert model.name == strawberry.Some("Ada")
    assert model.phone == strawberry.Some("555")
    assert model.address == strawberry.Some(AddressInput(zip_code="12345"))
    assert model.tags == strawberry.Some(["admin"])
    assert model.model_fields_set == {"name", "phone", "address", "tags"}
    assert model.model_dump(exclude_unset=True) == {
        "name": "Ada",
        "phone": "555",
        "address": {"zip_code": "12345"},
        "tags": ["admin"],
    }


def test_null_is_some_none_when_the_type_allows_it():
    model = update_user({"phone": None, "address": None})

    assert model.phone == strawberry.Some(None)
    assert model.address == strawberry.Some(None)
    assert model.name is None
    assert model.model_fields_set == {"phone", "address"}
    assert model.model_dump(exclude_unset=True) == {"phone": None, "address": None}


@pytest.mark.parametrize(
    ("query", "variables"),
    [
        pytest.param(
            "mutation { updateUser(input: { name: null }) { ... on User { name } } }",
            None,
            id="literal",
        ),
        pytest.param(UPDATE_USER, {"input": {"name": None}}, id="variable"),
    ],
)
def test_null_is_an_error_when_the_type_does_not_allow_it(
    query: str, variables: dict[str, Any] | None
):
    """Like on `@strawberry.input`, null isn't a value of `Maybe[T]`."""
    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert "Field of type 'Maybe[str]' cannot be explicitly set to null" in str(
        result.errors[0]
    ) or "Field 'name' of type 'Maybe[str]' cannot be explicitly set to null" in str(
        result.errors[0]
    )
    assert "Use 'Maybe[str | None]' if you need to allow null values" in str(
        result.errors[0]
    )


def test_invalid_values_are_reported_at_the_field():
    result = schema.execute_sync(
        UPDATE_USER,
        variable_values={
            "input": {"name": "a", "address": {"zipCode": "x"}, "tags": ["ok"]}
        },
    )

    assert not result.errors
    assert result.data == snapshot(
        {
            "updateUser": {
                "errors": [
                    {
                        "location": ["input", "name"],
                        "message": "String should have at least 2 characters",
                        "type": "string_too_short",
                    },
                    {
                        "location": ["input", "address", "zipCode"],
                        "message": "String should match pattern '^\\d{5}$'",
                        "type": "string_pattern_mismatch",
                    },
                ]
            }
        }
    )


def test_lists_of_inputs():
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        items: strawberry.Maybe[list[ItemInput]]

    @strawberry.type
    class Order:
        total: int

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> Order | ValidationError:
            if input.items is None:
                return Order(total=-1)

            return Order(total=sum(item.quantity for item in input.items.value))

    schema = strawberry.Schema(
        query=Query, exception_handlers=[PydanticValidationErrorHandler()]
    )
    query = """
        query ($input: OrderInput!) {
            order(input: $input) {
                ... on Order { total }
                ... on ValidationError { errors { location type } }
            }
        }
    """

    assert str(schema) == snapshot('''\
input ItemInput {
  quantity: Int!
}

type Order {
  total: Int!
}

input OrderInput {
  items: [ItemInput!]
}

union OrderValidationError = Order | ValidationError

type Query {
  order(input: OrderInput!): OrderValidationError!
}

"""The inputs failed validation."""
type ValidationError {
  """The problems with the input values."""
  errors: [ValidationErrorDetail!]!
}

"""A problem with an input value."""
type ValidationErrorDetail {
  """The argument, then field names and list indexes, all as strings."""
  location: [String!]!

  """The reason the value is invalid."""
  message: String!

  """The Pydantic error type, like `string_too_short`."""
  type: String!
}\
''')

    result = schema.execute_sync(query, variable_values={"input": {}})
    assert not result.errors
    assert result.data == {"order": {"total": -1}}

    result = schema.execute_sync(
        query, variable_values={"input": {"items": [{"quantity": 1}, {"quantity": 2}]}}
    )
    assert not result.errors
    assert result.data == {"order": {"total": 3}}

    result = schema.execute_sync(
        query, variable_values={"input": {"items": [{"quantity": 1}, {"quantity": 0}]}}
    )
    assert not result.errors
    assert result.data == {
        "order": {
            "errors": [
                {
                    "location": ["input", "items", "1", "quantity"],
                    "type": "greater_than",
                }
            ]
        }
    }


def test_strict_models_get_tuples():
    """Lists in a `Maybe` are converted like in other fields."""

    @strawberry.pydantic.input
    class PointInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)

        coordinates: strawberry.Maybe[tuple[int, int]]

    @strawberry.type
    class Query:
        @strawberry.field
        def point(self, input: PointInput) -> str:
            return repr(input.coordinates)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ point(input: { coordinates: [1, 2] }) }")

    assert not result.errors
    assert result.data == {"point": "Some((1, 2))"}


def test_one_of_inputs():
    @strawberry.pydantic.input(one_of=True)
    class SearchInput(pydantic.BaseModel):
        name: strawberry.Maybe[str]
        id: strawberry.Maybe[int]

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, by: SearchInput) -> str:
            return repr(by)

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
directive @oneOf on INPUT_OBJECT

type Query {
  search(by: SearchInput!): String!
}

input SearchInput @oneOf {
  name: String
  id: Int
}\
""")

    result = schema.execute_sync("{ search(by: { id: 1 }) }")

    assert not result.errors
    assert result.data == {"search": "SearchInput(name=None, id=Some(1))"}


def test_argument_defaults():
    """A `Maybe` field of a model used as a default is printed when it's set."""

    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        name: strawberry.Maybe[str]
        active: strawberry.Maybe[bool | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self, filter: FilterInput = FilterInput(active=None)) -> str:
            return repr(filter)

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
input FilterInput {
  name: String
  active: Boolean
}

type Query {
  users(filter: FilterInput! = { active: null }): String!
}\
""")

    result = schema.execute_sync("{ users }")

    assert not result.errors
    assert result.data == {"users": "FilterInput(name=None, active=Some(None))"}


def test_fields_inherited_from_strawberry_inputs():
    @strawberry.input
    class ChangesInput:
        name: strawberry.Maybe[str]

    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel, ChangesInput):
        age: strawberry.Maybe[int]

    @strawberry.type
    class Query:
        @strawberry.field
        def update(self, input: UpdateInput) -> str:
            return repr(input)

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  update(input: UpdateInput!): String!
}

input UpdateInput {
  name: String
  age: Int
}\
""")

    result = schema.execute_sync('{ update(input: { name: "Ada" }) }')

    assert not result.errors
    assert result.data == {"update": "UpdateInput(name=Some('Ada'), age=None)"}


def test_models_can_be_used_in_python():
    """The model works like it does with GraphQL: a key is a field that was sent."""
    model = UpdateUserInput()
    assert model.name is None
    assert model.model_fields_set == set()
    assert model.model_dump() == {
        "name": None,
        "phone": None,
        "address": None,
        "tags": None,
    }

    model = UpdateUserInput(name="ada", phone=None)
    assert model.name == strawberry.Some("Ada")
    assert model.phone == strawberry.Some(None)
    assert model.model_fields_set == {"name", "phone"}

    # `Some` values are validated too
    model = UpdateUserInput(
        name=strawberry.Some("ada"), address=strawberry.Some({"zip_code": "12345"})
    )
    assert model.name == strawberry.Some("Ada")
    assert model.address == strawberry.Some(AddressInput(zip_code="12345"))
    assert model.model_dump(mode="json", exclude_unset=True) == {
        "name": "Ada",
        "address": {"zip_code": "12345"},
    }

    model = UpdateUserInput.model_validate_json('{"name": "ada", "phone": null}')
    assert model.name == strawberry.Some("Ada")
    assert model.phone == strawberry.Some(None)

    with pytest.raises(pydantic.ValidationError) as error:
        UpdateUserInput(name=None)

    assert error.value.errors(include_url=False) == [
        {
            "type": "string_type",
            "loc": ("name",),
            "msg": "Input should be a valid string",
            "input": None,
        }
    ]


def test_fields_are_not_required():
    assert not UpdateUserInput.model_fields["name"].is_required()
    assert UpdateUserInput.model_fields["name"].default is None
    assert UpdateUserInput.model_construct().name is None
    parameters = inspect.signature(UpdateUserInput).parameters
    assert list(parameters) == ["name", "phone", "address", "tags"]
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        and parameter.default is None
        and get_origin(parameter.annotation) is strawberry.Maybe
        for parameter in parameters.values()
    )
    assert parameters["phone"].annotation == strawberry.Maybe[str | None]


def test_json_schema():
    assert UpdateUserInput.model_json_schema() == snapshot(
        {
            "$defs": {
                "AddressInput": {
                    "properties": {
                        "zip_code": {
                            "pattern": "^\\d{5}$",
                            "title": "Zip Code",
                            "type": "string",
                        }
                    },
                    "required": ["zip_code"],
                    "title": "AddressInput",
                    "type": "object",
                }
            },
            "properties": {
                "name": {
                    "default": None,
                    "minLength": 2,
                    "title": "Name",
                    "type": "string",
                },
                "phone": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "Phone",
                },
                "address": {
                    "anyOf": [{"$ref": "#/$defs/AddressInput"}, {"type": "null"}],
                    "default": None,
                },
                "tags": {
                    "default": None,
                    "items": {"type": "string"},
                    "title": "Tags",
                    "type": "array",
                },
            },
            "title": "UpdateUserInput",
            "type": "object",
        }
    )


@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=r"Field `name` on pydantic type `User` can't use `strawberry\.Maybe`",
)
def test_output_types_cannot_use_maybe():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: strawberry.Maybe[str]


@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=r"Field `name` on pydantic type `Node` can't use `strawberry\.Maybe`",
)
def test_interfaces_cannot_use_maybe():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        name: strawberry.Maybe[str]


@pytest.mark.parametrize(
    "default",
    [
        pytest.param("Ada", id="value"),
        pytest.param(strawberry.Some("Ada"), id="some"),
        pytest.param(strawberry.UNSET, id="unset"),
        pytest.param(pydantic.Field(default_factory=lambda: None), id="factory"),
    ],
)
@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Field `name` on pydantic input `UpdateInput` can't use "
        r"`strawberry\.Maybe` with a default"
    ),
)
def test_maybe_fields_cannot_have_a_default(default: Any):
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: strawberry.Maybe[str] = default


@pytest.mark.parametrize(
    "annotation",
    [
        pytest.param(
            lambda: Annotated[strawberry.Maybe[int], pydantic.Field(ge=0)],
            id="constraint",
        ),
        pytest.param(
            lambda: Annotated[
                strawberry.Maybe[int], pydantic.AfterValidator(lambda v: v)
            ],
            id="validator",
        ),
    ],
)
@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Field `age` on pydantic input `UpdateInput` has metadata outside its "
        r"`strawberry\.Maybe`"
    ),
)
def test_metadata_outside_maybe_is_an_error(annotation: Any):
    """Pydantic would apply it to the `Some`, not to the value in it."""

    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        age: annotation()


@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Field `age` on pydantic input `UpdateInput` has metadata outside its "
        r"`strawberry\.Maybe`"
    ),
)
def test_constraints_of_field_defaults_are_outside_maybe():
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        age: strawberry.Maybe[int] = pydantic.Field(None, ge=0)


def test_field_options_without_metadata():
    """`strawberry.field()` and the options of `pydantic.Field()` can be outside."""

    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: Annotated[
            strawberry.Maybe[str], strawberry.field(name="fullName", description="Name")
        ]
        age: strawberry.Maybe[Annotated[int, pydantic.Field(ge=0)]] = pydantic.Field(
            None, description="Age"
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def update(self, input: UpdateInput) -> str:
            return repr(input)

    schema = strawberry.Schema(
        query=Query, exception_handlers=[PydanticValidationErrorHandler()]
    )

    assert str(schema) == snapshot("""\
type Query {
  update(input: UpdateInput!): String!
}

input UpdateInput {
  \"\"\"Name\"\"\"
  fullName: String

  \"\"\"Age\"\"\"
  age: Int
}\
""")

    result = schema.execute_sync('{ update(input: { fullName: "Ada", age: 3 }) }')
    assert not result.errors
    assert result.data == {"update": "UpdateInput(name=Some('Ada'), age=Some(3))"}

    result = schema.execute_sync("{ update(input: { age: -1 }) }")
    assert result.errors
    assert (
        "Invalid input: input.age: Input should be greater than or equal to 0"
        in str(result.errors[0])
    )


def test_maybe_fields_can_have_an_explicit_none_default():
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: strawberry.Maybe[str] = None

    assert UpdateInput().name is None
    assert UpdateInput(name="Ada").name == strawberry.Some("Ada")


@pytest.mark.parametrize("where", ["field", "model"])
@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Pydantic input `UpdateInput` can't validate the default of "
        r"`strawberry\.Maybe` field `name`"
    ),
)
def test_explicit_none_defaults_cannot_be_validated(where: str):
    """Pydantic would validate `None` as a value sent by the client."""
    if where == "field":

        @strawberry.pydantic.input
        class UpdateInput(pydantic.BaseModel):
            name: strawberry.Maybe[str] = pydantic.Field(None, validate_default=True)

    else:

        @strawberry.pydantic.input
        class UpdateInput(pydantic.BaseModel):  # type: ignore[no-redef]
            model_config = pydantic.ConfigDict(validate_default=True)

            name: strawberry.Maybe[str] = None


def test_validate_default_does_not_apply_to_fields_without_a_default():
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(validate_default=True)

        name: strawberry.Maybe[str]
        phone: strawberry.Maybe[str | None]

    model = UpdateInput()

    assert model.name is None
    assert model.phone is None

    # the `None` default the decorator adds isn't validated either when the
    # schema is built again
    assert UpdateInput.model_fields["name"].validate_default is False
    UpdateInput.model_rebuild(force=True)

    model = UpdateInput()

    assert model.name is None
    assert model.phone is None


def test_subclasses_keep_the_fields_optional():
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(validate_default=True)

        name: strawberry.Maybe[str]

    @strawberry.pydantic.input
    class UpdateAdminInput(UpdateInput):
        role: strawberry.Maybe[str | None]

    model = UpdateAdminInput()

    assert model.name is None
    assert model.role is None
    assert UpdateAdminInput(name="Ada", role=None).model_dump(exclude_unset=True) == {
        "name": "Ada",
        "role": None,
    }


@pytest.mark.parametrize("mode", ["after", "plain"])
@pytest.mark.raises_strawberry_exception(
    MaybeFieldError,
    match=(
        r"Field `name` on pydantic input `UpdateInput` has a field validator "
        r"outside its `strawberry\.Maybe`"
    ),
)
def test_field_validators_outside_maybe_are_an_error(mode: str):
    """An `after` validator would get the `Some`, a `plain` one replace it."""

    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: strawberry.Maybe[str]

        @pydantic.field_validator("name", mode=mode)
        @classmethod
        def check_name(cls, value: Any) -> Any:
            return value


def test_before_and_wrap_field_validators_get_the_value():
    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: strawberry.Maybe[str]
        nickname: strawberry.Maybe[str | None]

        @pydantic.field_validator("name", mode="before")
        @classmethod
        def strip_name(cls, value: Any) -> Any:
            return value.strip()

        @pydantic.field_validator("nickname", mode="wrap")
        @classmethod
        def check_nickname(
            cls, value: Any, handler: pydantic.ValidatorFunctionWrapHandler
        ) -> Any:
            assert value is None or isinstance(value, str)
            return handler(value)

    model = UpdateInput(name="  Ada ", nickname=None)

    assert model.name == strawberry.Some("Ada")
    assert model.nickname == strawberry.Some(None)
    assert UpdateInput().name is None


def test_wildcard_field_validators_get_the_some():
    """`field_validator("*")` isn't about the `Maybe` fields, so it isn't an error."""
    seen: list[Any] = []

    @strawberry.pydantic.input
    class UpdateInput(pydantic.BaseModel):
        name: strawberry.Maybe[str]
        age: int = 0

        @pydantic.field_validator("*")
        @classmethod
        def record(cls, value: Any) -> Any:
            seen.append(value)
            return value

    assert UpdateInput(name="Ada", age=3).name == strawberry.Some("Ada")
    assert seen == [strawberry.Some("Ada"), 3]
    assert UpdateInput().name is None
