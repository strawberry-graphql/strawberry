import warnings
from typing import Annotated, Any

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.permission import PermissionExtension
from strawberry.pydantic.exceptions import (
    StrawberryFieldAsDefaultError,
    UnregisteredTypeException,
)
from strawberry.scalars import JSON
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
    """Test that Pydantic field aliases aren't used as GraphQL names."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(alias="userAge")]
        name: Annotated[str, pydantic.Field(alias="userName")]

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name is None
    assert name_field.graphql_name is None


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
            r"`User\.address` uses `Address`, which isn't a Strawberry type: "
            r"decorate it with `@strawberry\.pydantic\.type`"
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
    assert age_field.graphql_name is None
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


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


def _query_email(user_type: type, user: object) -> strawberry.types.ExecutionResult:
    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> user_type:  # type: ignore[valid-type]
            return user

    schema = strawberry.Schema(query=Query, types=[user_type])

    return schema.execute_sync("{ user { email } }")


def test_annotated_permissions_are_attached_once():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        email: Annotated[str, strawberry.field(permission_classes=[IsAdmin])]

    [email_field] = get_object_definition(User, strict=True).fields

    assert email_field.permission_classes == [IsAdmin]
    assert [type(extension) for extension in email_field.extensions] == [
        PermissionExtension
    ]


def test_annotated_permissions_declared_on_a_base_model_are_enforced():
    class UserBase(pydantic.BaseModel):
        email: Annotated[str, strawberry.field(permission_classes=[IsAdmin])]

    @strawberry.pydantic.type
    class User(UserBase):
        name: str

    result = _query_email(User, User(name="Ada", email="ada@example.com"))

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_annotated_permissions_declared_on_a_pydantic_interface_are_enforced():
    @strawberry.pydantic.interface
    class Account(pydantic.BaseModel):
        email: Annotated[str, strawberry.field(permission_classes=[IsAdmin])]

    @strawberry.pydantic.type
    class User(Account):
        name: str

    result = _query_email(User, User(name="Ada", email="ada@example.com"))

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_fields_declared_on_a_strawberry_interface_keep_their_configuration():
    @strawberry.interface
    class Account:
        email: str = strawberry.field(permission_classes=[IsAdmin])

    @strawberry.pydantic.type
    class User(pydantic.BaseModel, Account):
        name: str

    result = _query_email(User, User(name="Ada", email="ada@example.com"))

    assert result.data is None
    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_redeclared_fields_override_the_strawberry_interface_configuration():
    # same as @strawberry.type: redeclaring a field replaces the inherited one
    @strawberry.interface
    class Account:
        email: str = strawberry.field(permission_classes=[IsAdmin])

    @strawberry.pydantic.type
    class User(pydantic.BaseModel, Account):
        name: str
        email: str

    result = _query_email(User, User(name="Ada", email="ada@example.com"))

    assert not result.errors
    assert result.data == {"user": {"email": "ada@example.com"}}


def test_annotated_graphql_type_is_used():
    @strawberry.pydantic.type
    class Settings(pydantic.BaseModel):
        values: Annotated[dict[str, Any], strawberry.field(graphql_type=JSON)]

    @strawberry.type
    class Query:
        @strawberry.field
        def settings(self) -> Settings:
            return Settings(values={"theme": "dark"})

    schema = strawberry.Schema(query=Query)

    assert "values: JSON!" in str(schema)

    result = schema.execute_sync("{ settings { values } }")

    assert not result.errors
    assert result.data == {"settings": {"values": {"theme": "dark"}}}


def test_multiple_strawberry_fields_in_annotated_raise_an_error():
    with pytest.raises(MultipleStrawberryFieldsError):

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: Annotated[
                str,
                strawberry.field(description="first"),
                strawberry.field(description="second"),
            ]


def test_nested_strawberry_field_in_annotated_raises_an_error():
    with pytest.raises(InvalidStrawberryFieldAnnotationError):

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            tags: list[Annotated[str, strawberry.field(description="nested")]]


def test_strawberry_field_as_default_value_raises_an_error():
    with pytest.raises(
        StrawberryFieldAsDefaultError,
        match=(
            r"`strawberry.field\(\)` can't be used as the default value of field "
            r"`email` on pydantic model `User`"
        ),
    ):

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            email: str = strawberry.field(permission_classes=[IsAdmin])


def test_deprecated_fields():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        old_name: str = pydantic.Field(default="", deprecated="Use name")
        nickname: Annotated[
            str, strawberry.field(deprecation_reason="Use name, really")
        ] = pydantic.Field(default="", deprecated="Use name")
        alias: str = pydantic.Field(default="", deprecated=True)

        @pydantic.computed_field(deprecated="Use name")
        @property
        def display_name(self) -> str:
            return self.name

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Ada", old_name="ada", nickname="A")

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  user: User!
}

type User {
  name: String!
  oldName: String! @deprecated(reason: "Use name")
  nickname: String! @deprecated(reason: "Use name, really")
  alias: String! @deprecated
  displayName: String! @deprecated(reason: "Use name")
}\
""")

    with warnings.catch_warnings():
        # pydantic warns when deprecated fields are read
        warnings.simplefilter("ignore", DeprecationWarning)

        result = schema.execute_sync("{ user { oldName nickname displayName } }")

    assert not result.errors
    assert result.data == {
        "user": {"oldName": "ada", "nickname": "A", "displayName": "Ada"}
    }


def test_deprecated_input_fields_are_not_deprecated_in_graphql():
    # GraphQL doesn't allow deprecating required input fields
    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str = pydantic.Field(deprecated="Use full_name")

    [field] = get_object_definition(UserInput, strict=True).fields

    assert field.deprecation_reason is None
