import sys
from collections.abc import Callable
from typing import Optional

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic.exceptions import (
    ModelAlreadyDecoratedError,
    NotAPydanticModelError,
    UnsupportedRootModelError,
)
from strawberry.types.base import (
    StrawberryOptional,
    get_object_definition,
)


def test_basic_type_includes_all_fields():
    """Test that @strawberry.pydantic.type includes all fields from the model."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    definition = get_object_definition(User, strict=True)
    assert definition.name == "User"

    # Should have two fields
    assert len(definition.fields) == 2

    # Find fields by name
    age_field = next(f for f in definition.fields if f.python_name == "age")
    password_field = next(f for f in definition.fields if f.python_name == "password")

    assert age_field.python_name == "age"
    assert age_field.graphql_name is None
    assert age_field.type is int

    assert password_field.python_name == "password"
    assert password_field.graphql_name is None
    assert isinstance(password_field.type, StrawberryOptional)
    assert password_field.type.of_type is str


def test_basic_type_with_name_override():
    """Test that @strawberry.pydantic.type with name parameter works."""

    @strawberry.pydantic.type(name="CustomUser")
    class User(pydantic.BaseModel):
        age: int

    definition = get_object_definition(User, strict=True)
    assert definition.name == "CustomUser"


def test_basic_type_with_description():
    """Test that @strawberry.pydantic.type with description parameter works."""

    @strawberry.pydantic.type(description="A user model")
    class User(pydantic.BaseModel):
        age: int

    definition = get_object_definition(User, strict=True)
    assert definition.description == "A user model"


def test_resolvers_can_return_objects_with_the_same_attributes():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

    class UserRow:
        # e.g. a row of an ORM
        name = "Ada"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return UserRow()  # type: ignore[return-value]

    result = strawberry.Schema(query=Query).execute_sync("{ user { name } }")

    assert not result.errors
    assert result.data == {"user": {"name": "Ada"}}


def test_models_can_define_is_type_of():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

        @classmethod
        def is_type_of(cls, obj: object, info: object) -> bool:
            return isinstance(obj, cls)

    class UserRow:
        name = "Ada"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return UserRow()  # type: ignore[return-value]

    result = strawberry.Schema(query=Query).execute_sync("{ user { name } }")

    assert result.errors
    assert "Expected value of type 'User'" in result.errors[0].message


def test_objects_cast_to_a_type_implementing_an_interface():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.pydantic.type
    class User(Node):
        name: str

    class UserRow:
        id = "1"
        name = "Ada"

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return strawberry.cast(User, UserRow())

    result = strawberry.Schema(query=Query, types=[User]).execute_sync(
        "{ node { id ... on User { name } } }"
    )

    assert not result.errors
    assert result.data == {"node": {"id": "1", "name": "Ada"}}


def test_schema_generation():
    """Test that the decorated models work in schema generation."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(age=25, name="John")

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> User:
            return User(age=input.age, name=input.name)

    # Test that schema can be created successfully
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    assert schema is not None

    assert str(schema) == snapshot(
        """\
input CreateUserInput {
  age: Int!
  name: String!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
}

type Query {
  getUser: User!
}

type User {
  age: Int!
  name: String!
}\
"""
    )


@pytest.mark.parametrize(
    "decorator",
    [
        strawberry.pydantic.type,
        strawberry.pydantic.input,
        strawberry.pydantic.interface,
    ],
    ids=["type", "input", "interface"],
)
def test_decorating_a_class_that_is_not_a_pydantic_model_raises_an_error(
    decorator: Callable[[type], type],
):
    name = decorator.__name__

    with pytest.raises(
        NotAPydanticModelError,
        match=(
            rf"strawberry\.pydantic\.{name} can only be used with pydantic models, "
            r"but `User` is not a subclass of `pydantic\.BaseModel`"
        ),
    ):

        @decorator
        class User:
            name: str


@pytest.mark.raises_strawberry_exception(
    NotAPydanticModelError,
    match=(
        r"strawberry\.pydantic\.type can only be used with pydantic models, but "
        r"`User` is not a subclass of `pydantic\.BaseModel`"
    ),
)
def test_decorating_a_pydantic_dataclass_raises_an_error():
    @strawberry.pydantic.type
    @pydantic.dataclasses.dataclass
    class User:
        name: str


@pytest.mark.parametrize(
    "decorator",
    [
        strawberry.pydantic.type,
        strawberry.pydantic.input,
        strawberry.pydantic.interface,
    ],
    ids=["type", "input", "interface"],
)
def test_decorating_a_root_model_raises_an_error(decorator: Callable[[type], type]):
    name = decorator.__name__

    with pytest.raises(
        UnsupportedRootModelError,
        match=(
            rf"`Tags` is a `RootModel`, which can't be used with "
            rf"`strawberry\.pydantic\.{name}`"
        ),
    ):

        @decorator
        class Tags(pydantic.RootModel[list[str]]):
            pass


@pytest.mark.raises_strawberry_exception(
    UnsupportedRootModelError,
    match=(
        r"`Tags` is a `RootModel`, which can't be used with "
        r"`strawberry\.pydantic\.input`"
    ),
)
def test_root_model_error():
    @strawberry.pydantic.input
    class Tags(pydantic.RootModel[list[str]]):
        pass


class Tags(pydantic.RootModel[list[str]]):
    pass


@pytest.mark.raises_strawberry_exception(
    UnsupportedRootModelError,
    match=(
        r"`Post\.tags` uses `Tags`, which is a `RootModel` and can't be a GraphQL "
        r"type"
    ),
)
def test_root_model_fields_raise_an_error():
    @strawberry.pydantic.type
    class Post(pydantic.BaseModel):
        tags: Tags


def test_root_model_errors_render_brackets():
    rich_console = pytest.importorskip("rich.console")

    with pytest.raises(UnsupportedRootModelError) as exc_info:

        @strawberry.pydantic.input
        class PostInput(pydantic.BaseModel):
            ids: pydantic.RootModel[list[int]]

    console = rich_console.Console(width=200, color_system=None)

    with console.capture() as capture:
        console.print(exc_info.value)

    output = capture.get()

    assert "`PostInput.ids` uses `RootModel[list[int]]`" in output
    assert "for example `list[str]` for `RootModel[list[str]]`" in output


@pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason="Pydantic v1 is not compatible with Python 3.14+",
)
def test_decorating_a_pydantic_v1_model_raises_an_error():
    from pydantic import v1 as pydantic_v1

    with pytest.raises(
        NotAPydanticModelError,
        match=(
            r"`User` is a pydantic v1 model, but strawberry\.pydantic\.type only "
            r"supports pydantic v2 models"
        ),
    ):

        @strawberry.pydantic.type
        class User(pydantic_v1.BaseModel):
            name: str


@pytest.mark.raises_strawberry_exception(
    ModelAlreadyDecoratedError,
    match=(
        r"`Address` is already a type, so it can't be decorated with "
        r"`strawberry\.pydantic\.type`"
    ),
)
def test_decorating_a_model_twice_raises_an_error():
    @strawberry.pydantic.type
    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        street: str


def test_models_can_only_be_decorated_once():
    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        street: str

    with pytest.raises(
        ModelAlreadyDecoratedError,
        match=(
            r"`Address` is already a type, so it can't be decorated with "
            r"`strawberry\.pydantic\.input`"
        ),
    ) as exc_info:
        strawberry.pydantic.input(Address)

    assert exc_info.value.suggestion.startswith(
        "To use a model both as an output type and as an input, decorate a subclass"
    )

    # a subclass can be used as the input
    @strawberry.pydantic.input
    class AddressInput(Address):
        pass

    assert get_object_definition(AddressInput, strict=True).is_input
    assert not get_object_definition(Address, strict=True).is_input


async def test_objects_cast_in_unions():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str = pydantic.Field(min_length=1)

    class UserRow:
        name = "Ada"

    @strawberry.type
    class Query:
        hello: str = "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def create_user(
            self, input: UserInput
        ) -> User | strawberry.pydantic.ValidationError:
            return strawberry.cast(User, UserRow())

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[strawberry.pydantic.PydanticValidationErrorHandler()],
    )

    result = await schema.execute(
        'mutation { createUser(input: {name: "Ada"}) { ... on User { name } } }'
    )

    assert not result.errors
    assert result.data == {"createUser": {"name": "Ada"}}
