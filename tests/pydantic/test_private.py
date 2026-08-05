import pydantic
from inline_snapshot import snapshot

import strawberry
from strawberry.types.base import get_object_definition


def test_strawberry_private_fields():
    """Test that strawberry.Private fields are excluded from the GraphQL schema."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        age: int
        password: strawberry.Private[str]

    definition = get_object_definition(User, strict=True)
    assert definition.name == "User"

    # Should have three fields (id, name, age) - password should be excluded
    assert len(definition.fields) == 3

    field_names = {f.python_name for f in definition.fields}
    assert field_names == {"id", "name", "age"}

    # password field should not be in the GraphQL schema
    assert "password" not in field_names

    # But the python object should still have the password field
    user = User(id=1, name="John", age=30, password="secret")
    assert user.id == 1
    assert user.name == "John"
    assert user.age == 30
    assert user.password == "secret"


def test_strawberry_private_fields_access():
    """Test that strawberry.Private fields can be accessed in Python code."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        password: strawberry.Private[str]

    definition = get_object_definition(User, strict=True)
    assert definition.name == "User"

    # Should have two fields (id, name) - password should be excluded
    assert len(definition.fields) == 2

    field_names = {f.python_name for f in definition.fields}
    assert field_names == {"id", "name"}

    # Test that the private field is still accessible on the instance
    user = User(id=1, name="John", password="secret")
    assert user.id == 1
    assert user.name == "John"
    assert user.password == "secret"

    # Test that we can use the private field in Python logic
    def has_password(user: User) -> bool:
        return bool(user.password)

    assert has_password(user) is True

    user_no_password = User(id=2, name="Jane", password="")
    assert has_password(user_no_password) is False


def test_strawberry_private_fields_not_in_schema():
    """Test that strawberry.Private fields are not exposed in GraphQL schema."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        password: strawberry.Private[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(id=1, name="John", password="secret123")

    schema = strawberry.Schema(query=Query)

    # Check that password field is not in the schema
    schema_str = str(schema)
    assert "password" not in schema_str
    assert "id: Int!" in schema_str
    assert "name: String!" in schema_str

    # Test that we can query the exposed fields
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
    assert result.data == snapshot({"getUser": {"id": 1, "name": "John"}})

    # Test that querying the private field fails
    query_with_private = """
        query {
            getUser {
                id
                name
                password
            }
        }
    """

    result = schema.execute_sync(query_with_private)
    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == snapshot(
        "Cannot query field 'password' on type 'User'."
    )
