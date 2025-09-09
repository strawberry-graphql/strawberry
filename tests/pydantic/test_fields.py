from typing import Annotated

import pytest
from inline_snapshot import snapshot

import pydantic
import strawberry
from strawberry.pydantic.exceptions import UnregisteredTypeException
from strawberry.schema_directive import Location
from strawberry.types.base import get_object_definition


def test_pydantic_field_descriptions():
    """Test that Pydantic field descriptions are preserved."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(description="The user's age")]
        name: Annotated[str, pydantic.Field(description="The user's name")]

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.description == "The user's age"
    assert name_field.description == "The user's name"


def test_pydantic_field_aliases():
    """Test that Pydantic field aliases are used as GraphQL names."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(alias="userAge")]
        name: Annotated[str, pydantic.Field(alias="userName")]

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name == "userAge"
    assert name_field.graphql_name == "userName"


def test_can_use_strawberry_types():
    """Test that Pydantic models can use Strawberry types."""

    @strawberry.type
    class Address:
        street: str
        city: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        address: Address

    definition = get_object_definition(User, strict=True)

    address_field = next(f for f in definition.fields if f.python_name == "address")

    assert address_field.type is Address

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def user() -> User:
            return User(
                name="Rabbit", address=Address(street="123 Main St", city="Wonderland")
            )

    schema = strawberry.Schema(query=Query)

    query = """query {
        user {
            name
            address {
                street
                city
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {
            "user": {
                "name": "Rabbit",
                "address": {"street": "123 Main St", "city": "Wonderland"},
            }
        }
    )


def test_all_models_need_to_marked_as_strawberry_types():
    class Address(pydantic.BaseModel):
        street: str
        city: str

    with pytest.raises(
        UnregisteredTypeException,
        match=(
            r"Cannot find a Strawberry Type for <class '([^']+)\.([^']+)'> did you forget to register it\?"
        ),
    ):

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: str
            address: Address


def test_field_directives_basic():
    """Test that strawberry.field() directives work with Pydantic models using Annotated."""

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[Sensitive(reason="PII")])]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    age_field = next(f for f in definition.fields if f.python_name == "age")

    # Name field should have no directives
    assert len(name_field.directives) == 0

    # Age field should have the Sensitive directive
    assert len(age_field.directives) == 1
    assert isinstance(age_field.directives[0], Sensitive)
    assert age_field.directives[0].reason == "PII"


def test_field_directives_multiple():
    """Test multiple directives on a single field."""

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Tag:
        name: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        email: Annotated[
            str,
            strawberry.field(directives=[Sensitive(reason="PII"), Tag(name="contact")]),
        ]

    definition = get_object_definition(User, strict=True)

    email_field = next(f for f in definition.fields if f.python_name == "email")

    # Email field should have both directives
    assert len(email_field.directives) == 2

    sensitive_directive = next(
        d for d in email_field.directives if isinstance(d, Sensitive)
    )
    tag_directive = next(d for d in email_field.directives if isinstance(d, Tag))

    assert sensitive_directive.reason == "PII"
    assert tag_directive.name == "contact"


def test_field_directives_with_pydantic_features():
    """Test that strawberry.field() directives work alongside Pydantic field features."""

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Range:
        min: int
        max: int

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(description="The user's name")]
        age: Annotated[
            int,
            pydantic.Field(alias="userAge", description="The user's age"),
            strawberry.field(directives=[Range(min=0, max=150)]),
        ]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    age_field = next(f for f in definition.fields if f.python_name == "age")

    # Name field should preserve Pydantic description
    assert name_field.description == "The user's name"
    assert len(name_field.directives) == 0

    # Age field should have both Pydantic features and Strawberry directive
    assert age_field.description == "The user's age"
    assert age_field.graphql_name == "userAge"
    assert len(age_field.directives) == 1
    assert isinstance(age_field.directives[0], Range)
    assert age_field.directives[0].min == 0
    assert age_field.directives[0].max == 150


def test_field_directives_override_description():
    """Test that strawberry.field() description overrides Pydantic description."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(description="Pydantic description")]
        age: Annotated[
            int,
            pydantic.Field(description="Pydantic age description"),
            strawberry.field(description="Strawberry description override"),
        ]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    age_field = next(f for f in definition.fields if f.python_name == "age")

    # Name field should use Pydantic description
    assert name_field.description == "Pydantic description"

    # Age field should use strawberry.field() description override
    assert age_field.description == "Strawberry description override"


def test_field_directives_with_permissions():
    """Test that strawberry.field() permissions work with Pydantic models."""

    class IsAuthenticated(strawberry.BasePermission):
        message = "User is not authenticated"

        def has_permission(self, source, info, **kwargs):  # noqa: ANN003
            return True  # Simplified for testing

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        email: Annotated[str, strawberry.field(permission_classes=[IsAuthenticated])]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    email_field = next(f for f in definition.fields if f.python_name == "email")

    # Name field should have no permissions
    assert len(name_field.permission_classes) == 0

    # Email field should have the permission
    assert len(email_field.permission_classes) == 1
    assert email_field.permission_classes[0] == IsAuthenticated


def test_field_directives_with_deprecation():
    """Test that strawberry.field() deprecation works with Pydantic models."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        old_field: Annotated[
            str, strawberry.field(deprecation_reason="Use name instead")
        ]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    old_field = next(f for f in definition.fields if f.python_name == "old_field")

    # Name field should not be deprecated
    assert name_field.deprecation_reason is None

    # Old field should be deprecated
    assert old_field.deprecation_reason == "Use name instead"


def test_field_directives_input_types():
    """Test that field directives work with Pydantic input types."""

    @strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
    class Validate:
        pattern: str

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: str
        email: Annotated[
            str, strawberry.field(directives=[Validate(pattern=r"^[^@]+@[^@]+\.[^@]+")])
        ]

    definition = get_object_definition(CreateUserInput, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")
    email_field = next(f for f in definition.fields if f.python_name == "email")

    # Name field should have no directives
    assert len(name_field.directives) == 0

    # Email field should have the validation directive
    assert len(email_field.directives) == 1
    assert isinstance(email_field.directives[0], Validate)
    assert email_field.directives[0].pattern == r"^[^@]+@[^@]+\.[^@]+"


def test_field_directives_graphql_name_override():
    """Test that strawberry.field() can override Pydantic field aliases for GraphQL names."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: Annotated[
            str,
            pydantic.Field(alias="pydantic_name"),
            strawberry.field(name="strawberry_name"),
        ]

    definition = get_object_definition(User, strict=True)

    name_field = next(f for f in definition.fields if f.python_name == "name")

    # strawberry.field() graphql_name should override Pydantic alias
    assert name_field.graphql_name == "strawberry_name"
