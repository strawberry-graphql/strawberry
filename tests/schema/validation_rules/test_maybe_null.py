from typing import Union

import strawberry


def test_maybe_null_validation_rule_input_fields():
    """Test MaybeNullValidationRule validates input object fields correctly."""

    @strawberry.input
    class TestInput:
        strict_field: strawberry.Maybe[str]  # Should reject null
        flexible_field: strawberry.Maybe[Union[str, None]]  # Should allow null

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "success"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test 1: Valid values should work
    result = schema.execute_sync("""
        mutation {
            test(input: { strictField: "hello", flexibleField: "world" })
        }
    """)
    assert not result.errors
    assert result.data == {"test": "success"}

    # Test 2: Flexible field can be null
    result = schema.execute_sync("""
        mutation {
            test(input: { strictField: "hello", flexibleField: null })
        }
    """)
    assert not result.errors
    assert result.data == {"test": "success"}

    # Test 3: Strict field cannot be null
    result = schema.execute_sync("""
        mutation {
            test(input: { strictField: null, flexibleField: "world" })
        }
    """)
    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert "Expected value of type 'str', found null" in str(error)
    assert "strictField" in str(error)
    assert "cannot be explicitly set to null" in str(error)
    assert "Use 'Maybe[str | None]'" in str(error)


def test_maybe_null_validation_rule_resolver_arguments():
    """Test MaybeNullValidationRule validates resolver arguments correctly."""

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self,
            query: strawberry.Maybe[str] = None,  # Should reject null
            filter_by: strawberry.Maybe[Union[str, None]] = None,  # Should allow null
        ) -> str:
            return "success"

    schema = strawberry.Schema(query=Query)

    # Test 1: Valid values should work
    result = schema.execute_sync("""
        query {
            search(query: "hello", filterBy: "world")
        }
    """)
    assert not result.errors
    assert result.data == {"search": "success"}

    # Test 2: Flexible argument can be null
    result = schema.execute_sync("""
        query {
            search(query: "hello", filterBy: null)
        }
    """)
    assert not result.errors
    assert result.data == {"search": "success"}

    # Test 3: Strict argument cannot be null
    result = schema.execute_sync("""
        query {
            search(query: null, filterBy: "world")
        }
    """)
    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert "Expected value of type 'str', found null" in str(error)
    assert "query" in str(error)
    assert "cannot be explicitly set to null" in str(error)
    assert "Use 'Maybe[str | None]'" in str(error)


def test_maybe_null_validation_rule_multiple_errors():
    """Test that multiple null violations are all reported."""

    @strawberry.input
    class TestInput:
        field1: strawberry.Maybe[str]
        field2: strawberry.Maybe[int]
        field3: strawberry.Maybe[Union[str, None]]  # This one allows null

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "success"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with multiple nulls - should get multiple errors
    result = schema.execute_sync("""
        mutation {
            test(input: { field1: null, field2: null, field3: null })
        }
    """)
    assert result.errors
    assert len(result.errors) == 2  # field1 and field2 should fail, field3 should pass

    error_messages = [str(error) for error in result.errors]
    assert any("field1" in msg for msg in error_messages)
    assert any("field2" in msg for msg in error_messages)
    # field3 should NOT generate an error because it allows null


def test_maybe_null_validation_rule_nested_input():
    """Test validation works with nested input objects."""

    @strawberry.input
    class NestedInput:
        value: strawberry.Maybe[str]

    @strawberry.input
    class TestInput:
        nested: NestedInput

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "success"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with null in nested input
    result = schema.execute_sync("""
        mutation {
            test(input: { nested: { value: null } })
        }
    """)
    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert "Expected value of type 'str', found null" in str(error)
    assert "value" in str(error)


def test_maybe_null_validation_rule_different_types():
    """Test validation works with different field types."""

    @strawberry.input
    class TestInput:
        string_field: strawberry.Maybe[str]
        int_field: strawberry.Maybe[int]
        bool_field: strawberry.Maybe[bool]
        list_field: strawberry.Maybe[list[str]]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "success"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test each field type with null
    test_cases = [
        ("stringField", "str"),
        ("intField", "int"),
        ("boolField", "bool"),
        ("listField", "list[str]"),
    ]

    for field_name, type_name in test_cases:
        result = schema.execute_sync(f"""
            mutation {{
                test(input: {{ {field_name}: null }})
            }}
        """)
        assert result.errors
        assert len(result.errors) == 1
        error = result.errors[0]
        assert f"Expected value of type '{type_name}', found null" in str(error)


def test_maybe_null_validation_rule_custom_graphql_names():
    """Test validation works with custom GraphQL field names."""

    @strawberry.input
    class TestInput:
        internal_name: strawberry.Maybe[str] = strawberry.field(name="customName")

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "success"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with custom GraphQL name
    result = schema.execute_sync("""
        mutation {
            test(input: { customName: null })
        }
    """)
    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert "customName" in str(error)


# TODO: Add test for auto_camel_case=False configuration
# This requires accessing the schema configuration from the validation rule context,
# which needs further investigation of the GraphQL validation context API.
