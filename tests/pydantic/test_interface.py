import pydantic
from inline_snapshot import snapshot

import strawberry
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
        def get_user(self) -> User:
            return User(id="user_1", name="John")

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUser {
                id
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot({"getUser": {"id": "user_1", "name": "John"}})
