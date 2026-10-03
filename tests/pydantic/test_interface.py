import re

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.exceptions import InvalidSuperclassInterfaceError
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
