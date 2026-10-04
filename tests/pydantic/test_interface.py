import re
from typing import Generic, TypeVar

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.pydantic.exceptions import ModelAlreadyDecoratedError
from strawberry.types.base import get_object_definition


def test_basic_interface_type():
    """Test that @strawberry.pydantic.interface works."""

    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    definition = get_object_definition(Node, strict=True)

    assert definition.name == "Node"
    assert definition.is_interface is True
    assert len(definition.fields) == 1


def test_pydantic_interface_basic():
    """Test basic Pydantic interface functionality."""

    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    @strawberry.pydantic.type
    class User(Node):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return User(id="user_1", name="John")

    schema = strawberry.Schema(query=Query, types=[User])

    assert "type User implements Node" in str(schema)

    query = """
        query {
            node {
                __typename
                id
                ... on User {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {"node": {"__typename": "User", "id": "user_1", "name": "John"}}
    )


def test_interface_inherited_through_an_undecorated_model():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    # not decorated, but pydantic still gives its fields to subclasses
    class Timestamped(Node):
        created_at: str = "today"

    @strawberry.pydantic.type
    class User(Timestamped):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return User(id="user_1", name="John")

    interfaces = get_object_definition(User, strict=True).interfaces
    assert [interface.origin for interface in interfaces] == [Node]

    schema = strawberry.Schema(query=Query, types=[User])
    result = schema.execute_sync(
        "{ node { __typename id ... on User { name createdAt } } }"
    )

    assert not result.errors
    assert result.data == {
        "node": {
            "__typename": "User",
            "id": "user_1",
            "name": "John",
            "createdAt": "today",
        }
    }


@pytest.mark.raises_strawberry_exception(
    InvalidSuperclassInterfaceError,
    match=re.escape("Input class 'NodeInput' cannot inherit from interface(s): Node")
    + "$",
)
def test_input_cannot_inherit_from_an_interface():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    @strawberry.pydantic.input
    class NodeInput(Node):
        name: str


@pytest.mark.raises_strawberry_exception(
    InvalidSuperclassInterfaceError,
    match=re.escape("Input class 'NodeInput' cannot inherit from interface(s): Node")
    + "$",
)
def test_input_cannot_inherit_from_an_interface_through_an_undecorated_model():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    class Named(Node):
        name: str

    @strawberry.pydantic.input
    class NodeInput(Named):
        pass


def test_decorating_an_interface_as_an_input_suggests_a_shared_base():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    with pytest.raises(ModelAlreadyDecoratedError) as exc_info:
        strawberry.pydantic.input(Node)

    assert exc_info.value.suggestion == (
        "Inputs can't implement interfaces, so `Node` can't be subclassed for an "
        "input. Move the fields to share to an undecorated base model used by both "
        "instead, for example: `class NodeBase(BaseModel)`, with "
        "`@strawberry.pydantic.interface class Node(NodeBase)` and "
        "`@strawberry.pydantic.input class NodeInput(NodeBase)`."
    )


def test_decorating_an_implementation_as_an_input_suggests_a_shared_base():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.pydantic.type
    class User(Node):
        name: str

    with pytest.raises(ModelAlreadyDecoratedError) as exc_info:
        strawberry.pydantic.input(User)

    assert exc_info.value.suggestion == (
        "Inputs can't implement interfaces, so `User` can't be subclassed for an "
        "input. Move the fields to share to an undecorated base model used by both "
        "instead, for example: `class UserBase(BaseModel)`, with "
        "`@strawberry.pydantic.type class User(UserBase, Node)` and "
        "`@strawberry.pydantic.input class UserInput(UserBase)`."
    )


def test_shared_base_suggestion_keeps_the_parameters_of_generic_bases():
    T = TypeVar("T")

    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.pydantic.type
    class Page(Node, Generic[T]):
        items: list[T]

    with pytest.raises(ModelAlreadyDecoratedError) as exc_info:
        strawberry.pydantic.input(Page)

    assert (
        "`@strawberry.pydantic.type class Page(PageBase, Node, Generic[T])`"
        in exc_info.value.suggestion
    )


def test_interfaces_and_inputs_can_share_an_undecorated_base():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    class UserBase(pydantic.BaseModel):
        name: str

    @strawberry.pydantic.type
    class User(UserBase, Node):
        pass

    @strawberry.pydantic.input
    class UserInput(UserBase):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, input: UserInput) -> Node:
            return User(id="user_1", name=input.name)

    schema = strawberry.Schema(query=Query, types=[User])

    assert "type User implements Node" in str(schema)

    result = schema.execute_sync(
        '{ node(input: { name: "John" }) { id ... on User { name } } }'
    )

    assert not result.errors
    assert result.data == {"node": {"id": "user_1", "name": "John"}}


def test_inputs_can_share_the_bases_of_a_type_extending_an_implementation():
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: strawberry.ID

    class UserBase(pydantic.BaseModel):
        name: str

    @strawberry.pydantic.type
    class User(UserBase, Node):
        pass

    class AdminBase(UserBase):
        level: int

    @strawberry.pydantic.type
    class Admin(AdminBase, User):
        pass

    @strawberry.pydantic.input
    class AdminInput(AdminBase):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, input: AdminInput) -> Node:
            return Admin(id="admin_1", **input.model_dump())

    schema = strawberry.Schema(query=Query, types=[Admin])

    assert "type Admin implements Node" in str(schema)

    result = schema.execute_sync(
        '{ node(input: { name: "John", level: 1 }) { id ... on Admin { name level } } }'
    )

    assert not result.errors
    assert result.data == {"node": {"id": "admin_1", "name": "John", "level": 1}}
