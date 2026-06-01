"""
Tests for TypedDict support (output, input, nullability, nesting, and validation).
"""

from __future__ import annotations

import textwrap
from typing import Annotated, Optional, TypedDict
from typing_extensions import NotRequired, Required

import pytest

import strawberry
from strawberry.schema_directive import Location
from strawberry.typed_dict import TypedDictValidationError, validate_typed_dict


@strawberry.typed_dict
class Point2D(TypedDict):
    x: int
    y: int


@strawberry.typed_dict_input
class CreateUserInput(TypedDict):
    name: str
    age: int


@strawberry.typed_dict
class UserDictTotalFalse(TypedDict, total=False):
    name: str
    email: str


@strawberry.typed_dict
class UserDictRequired(TypedDict, total=False):
    id: Required[int]
    name: str
    email: NotRequired[str]


@strawberry.typed_dict
class UserDictOptional(TypedDict, total=False):
    id: Required[int]
    name: str


@strawberry.typed_dict
class AddressDict(TypedDict):
    city: str
    zipcode: str


@strawberry.typed_dict
class UserDictNested(TypedDict):
    name: str
    address: AddressDict


@strawberry.typed_dict
class Item(TypedDict):
    sku: str
    qty: int


@strawberry.typed_dict
class ExamplePrivateFields(TypedDict):
    visible: str
    _internal: str


@strawberry.typed_dict_input
class OptionalInput(TypedDict, total=False):
    required_field: Required[str]
    optional_field: NotRequired[int]


def test_basic_output_typed_dict():
    @strawberry.type
    class Query:
        @strawberry.field
        def get_point(self) -> Point2D:
            return {"x": 10, "y": 20}

    schema = strawberry.Schema(query=Query)

    query = "{ getPoint { x y } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["getPoint"] == {"x": 10, "y": 20}


def test_basic_input_typed_dict():
    @strawberry.type
    class Query:
        _dummy: str = "unused"  # at least one field needed

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, data: CreateUserInput) -> str:
            return f"Created {data['name']} (age {data['age']})"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    mutation = """
        mutation {
            createUser(data: {name: "John", age: 30})
        }
    """
    result = schema.execute_sync(mutation)
    assert not result.errors
    assert result.data["createUser"] == "Created John (age 30)"


def test_total_false_makes_fields_nullable():
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserDictTotalFalse:
            return {"name": "Alice"}

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent("""\
        type Query {
          user: UserDictTotalFalse!
        }

        type UserDictTotalFalse {
          name: String
          email: String
        }
    """).strip()

    assert str(schema) == expected


def test_required_and_not_required_fields():
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserDictRequired:
            return {"id": 1, "name": "Bob"}

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent("""\
        type Query {
          user: UserDictRequired!
        }

        type UserDictRequired {
          id: Int!
          name: String
          email: String
        }
    """).strip()

    assert str(schema) == expected


def test_missing_optional_key_resolves_to_null():
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserDictOptional:
            return {"id": 42}

    schema = strawberry.Schema(query=Query)

    query = "{ user { id name } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"] == {"id": 42, "name": None}


def test_nested_typed_dict():
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserDictNested:
            return {
                "name": "Carol",
                "address": {"city": "Springfield", "zipcode": "12345"},
            }

    schema = strawberry.Schema(query=Query)

    query = "{ user { name address { city zipcode } } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"] == {
        "name": "Carol",
        "address": {"city": "Springfield", "zipcode": "12345"},
    }


def test_list_of_typed_dict():
    @strawberry.type
    class Query:
        @strawberry.field
        def inventory(self) -> list[Item]:
            return [
                {"sku": "A1", "qty": 10},
                {"sku": "B2", "qty": 0},
            ]

    schema = strawberry.Schema(query=Query)

    query = "{ inventory { sku qty } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["inventory"] == [
        {"sku": "A1", "qty": 10},
        {"sku": "B2", "qty": 0},
    ]


def test_input_typed_dict_missing_optional_field():
    @strawberry.type
    class Query:
        _dummy: str = "unused"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def process(self, data: OptionalInput) -> str:
            req = data["required_field"]
            opt = data.get("optional_field", "missing")
            return f"req={req}, opt={opt}"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    mutation = """
        mutation {
            process(data: {requiredField: "hello"})
        }
    """
    result = schema.execute_sync(mutation)
    assert not result.errors
    assert result.data["process"] == "req=hello, opt=missing"


# Schema directive used for annotated metadata tests
@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class ExampleDirective:
    value: str


@strawberry.typed_dict
class AnnotatedUser(TypedDict):
    id: Annotated[int, "The unique identifier"]
    name: Annotated[
        str,
        strawberry.field(
            description="The user name", directives=[ExampleDirective(value="test")]
        ),
    ]


def test_annotated_metadata():
    @strawberry.type
    class Query:
        @strawberry.field
        def fetch_annotated(self) -> AnnotatedUser:
            return {"id": 1, "name": "Test"}

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent('''\
        type AnnotatedUser {
          """The unique identifier"""
          id: Int!

          """The user name"""
          name: String! @exampleDirective(value: "test")
        }
    ''').strip()

    assert expected in str(schema)


def test_validate_typed_dict_success():
    @strawberry.typed_dict
    class ValidDict(TypedDict):
        req: str
        opt: NotRequired[str]
        opt_type: Optional[int]

    validate_typed_dict(
        {
            "req": "hello",
            "opt": "world",
            "opt_type": 5,
        },
        ValidDict,
    )

    validate_typed_dict(
        {
            "req": "hello",
            "opt_type": None,
        },
        ValidDict,
    )

    validate_typed_dict(
        {
            "req": "hello",
            "opt_type": 1,
        },
        ValidDict,
    )


def test_validate_typed_dict_failure():
    @strawberry.typed_dict
    class MissingRequiredFieldDict(TypedDict):
        req1: str
        req2: int

    with pytest.raises(
        TypedDictValidationError,
        match="Missing required keys for MissingRequiredFieldDict: req2",
    ):
        validate_typed_dict(
            {"req1": "hello"},
            MissingRequiredFieldDict,
        )


def test_optional_value_does_not_make_key_optional():
    @strawberry.typed_dict
    class OptionalValueRequiredKeyDict(TypedDict):
        value: Optional[int]

    with pytest.raises(
        TypedDictValidationError,
        match="Missing required keys for OptionalValueRequiredKeyDict: value",
    ):
        validate_typed_dict({}, OptionalValueRequiredKeyDict)


def test_private_fields_are_ignored():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> ExamplePrivateFields:
            return {
                "visible": "hello",
                "_internal": "secret",
            }

    schema = strawberry.Schema(query=Query)

    expected = textwrap.dedent("""\
        type ExamplePrivateFields {
          visible: String!
        }

        type Query {
          example: ExamplePrivateFields!
        }
    """).strip()

    assert str(schema) == expected


def test_pep604_optional_union():
    @strawberry.typed_dict
    class Example(TypedDict):
        value: int | None

    validate_typed_dict(
        {"value": None},
        Example,
    )

    with pytest.raises(
        TypedDictValidationError,
        match="Missing required keys for Example: value",
    ):
        validate_typed_dict({}, Example)


def test_raises_error_on_non_typed_dict():
    with pytest.raises(TypeError, match="can only be applied to TypedDict classes"):

        @strawberry.typed_dict
        class NormalClass:
            name: str
