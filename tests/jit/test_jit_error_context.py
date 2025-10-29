"""Test enhanced error context with field names and types."""

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class User:
    id: str
    name: str

    @strawberry.field
    def error_field(self) -> str:
        """Field that always errors."""
        raise ValueError("This field always errors")

    @strawberry.field
    def nullable_error(self) -> str | None:
        """Nullable field that errors."""
        raise ValueError("Nullable field error")


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(id="1", name="John")


def test_error_includes_field_name_and_type():
    """Test that errors include field name and type in extensions."""
    schema = strawberry.Schema(query=Query)

    query = """
    {
        user {
            id
            errorField
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1

    error = result["errors"][0]

    # Check basic error structure
    assert "message" in error
    assert "path" in error
    assert error["path"] == ["user", "errorField"]

    # Check enhanced context in extensions
    assert "extensions" in error
    extensions = error["extensions"]

    assert "fieldName" in extensions
    assert extensions["fieldName"] == "errorField"

    assert "fieldType" in extensions
    assert extensions["fieldType"] == "String!"  # Non-nullable string

    assert "alias" in extensions
    assert extensions["alias"] == "errorField"  # No alias used


def test_error_context_with_alias():
    """Test that error context includes alias when present."""
    schema = strawberry.Schema(query=Query)

    query = """
    {
        user {
            id
            myError: errorField
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert "errors" in result
    error = result["errors"][0]

    # Path should use alias
    assert error["path"] == ["user", "myError"]

    # Extensions should show both field name and alias
    extensions = error["extensions"]
    assert extensions["fieldName"] == "errorField"
    assert extensions["alias"] == "myError"


def test_nullable_field_error_context():
    """Test error context for nullable fields."""
    schema = strawberry.Schema(query=Query)

    query = """
    {
        user {
            id
            nullableError
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Data should be partial (id present, nullableError null)
    assert result["data"]["user"]["id"] == "1"
    assert result["data"]["user"]["nullableError"] is None

    # Should have error with context
    assert "errors" in result
    error = result["errors"][0]

    extensions = error["extensions"]
    assert extensions["fieldName"] == "nullableError"
    assert extensions["fieldType"] == "String"  # Nullable (no !)


def test_multiple_errors_have_context():
    """Test that multiple errors all have enhanced context."""

    @strawberry.type
    class MultiErrorUser:
        id: str

        @strawberry.field
        def error1(self) -> str | None:
            raise ValueError("Error 1")

        @strawberry.field
        def error2(self) -> str | None:
            raise ValueError("Error 2")

    @strawberry.type
    class MultiErrorQuery:
        @strawberry.field
        def user(self) -> MultiErrorUser:
            return MultiErrorUser(id="1")

    schema = strawberry.Schema(query=MultiErrorQuery)

    query = """
    {
        user {
            id
            error1
            error2
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(MultiErrorQuery())

    # Should have 2 errors
    assert len(result["errors"]) == 2

    # Both should have enhanced context
    for error in result["errors"]:
        assert "extensions" in error
        assert "fieldName" in error["extensions"]
        assert "fieldType" in error["extensions"]

    # Check they have correct field names
    field_names = [e["extensions"]["fieldName"] for e in result["errors"]]
    assert "error1" in field_names
    assert "error2" in field_names
