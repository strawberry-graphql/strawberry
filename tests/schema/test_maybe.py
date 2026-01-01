from textwrap import dedent
from typing import Annotated

import pytest

import strawberry


@pytest.fixture
def maybe_schema() -> strawberry.Schema:
    @strawberry.type
    class User:
        name: str
        phone: str | None

    user = User(name="Patrick", phone=None)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return user

    @strawberry.input
    class UpdateUserInput:
        phone: strawberry.Maybe[str | None]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_user(self, input: UpdateUserInput) -> User:
            if input.phone:
                user.phone = input.phone.value
            return user

    return strawberry.Schema(query=Query, mutation=Mutation)


user_query = """
{
    user {
        phone
    }
}
"""


def set_phone(schema: strawberry.Schema, phone: str | None) -> dict:
    query = """
    mutation ($phone: String) {
        updateUser(input: { phone: $phone }) {
            phone
        }
    }
    """

    result = schema.execute_sync(query, variable_values={"phone": phone})
    assert not result.errors
    assert result.data
    return result.data["updateUser"]


def get_user(schema: strawberry.Schema) -> dict:
    result = schema.execute_sync(user_query)
    assert not result.errors
    assert result.data
    return result.data["user"]


def test_maybe(maybe_schema: strawberry.Schema) -> None:
    assert get_user(maybe_schema)["phone"] is None
    res = set_phone(maybe_schema, "123")
    assert res["phone"] == "123"


def test_maybe_some_to_none(maybe_schema: strawberry.Schema) -> None:
    assert get_user(maybe_schema)["phone"] is None
    set_phone(maybe_schema, "123")
    res = set_phone(maybe_schema, None)
    assert res["phone"] is None


def test_maybe_absent_value(maybe_schema: strawberry.Schema) -> None:
    set_phone(maybe_schema, "123")

    query = """
    mutation {
        updateUser(input: {}) {
            phone
        }
    }
    """
    result = maybe_schema.execute_sync(query)
    assert not result.errors
    assert result.data
    assert result.data["updateUser"]["phone"] == "123"
    # now check the reverse case.

    set_phone(maybe_schema, None)
    result = maybe_schema.execute_sync(query)
    assert not result.errors
    assert result.data
    assert result.data["updateUser"]["phone"] is None


def test_optional_argument_maybe() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: strawberry.Maybe[str | None] = None) -> str:
            if name:
                return "None" if name.value is None else name.value

            return "UNSET"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String): String!
        }"""
    )

    result = schema.execute_sync(
        """
        query {
            hello
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "UNSET"}
    result = schema.execute_sync(
        """
        query {
            hello(name: "bar")
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "bar"}
    result = schema.execute_sync(
        """
        query {
            hello(name: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "None"}


def test_maybe_list():
    @strawberry.input
    class InputData:
        items: strawberry.Maybe[list[str] | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, data: InputData) -> str:
            return "I am a test, and I received: " + str(data.items)

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        input InputData {
          items: [String!]
        }

        type Query {
          test(data: InputData!): String!
        }"""
    )


def test_maybe_str_rejects_explicit_nulls():
    """Test that Maybe[str] correctly rejects null values at Python validation level.

    BEHAVIOR:
    - Maybe[str] generates 'String' (optional) in GraphQL schema
    - Rejects null values at Python validation level, not GraphQL level
    - This allows the GraphQL parser to accept null, but Python validation rejects it
    """

    @strawberry.input
    class UpdateInput:
        name: strawberry.Maybe[str]  # Should be optional in schema but reject null

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update(self, input: UpdateInput) -> str:
            if input.name is not None:
                return f"Updated to: {input.name.value}"
            return "No change"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Generates optional field
    schema_str = str(schema)
    assert "name: String" in schema_str
    assert "name: String!" not in schema_str

    # Test with explicit null fails at Python validation level
    query = """
    mutation {
        update(input: { name: null })
    }
    """

    result = schema.execute_sync(query)
    assert result.errors
    assert len(result.errors) == 1
    # The error should mention Python-level validation, not GraphQL schema validation
    error_message = str(result.errors[0])
    assert "Expected value of type" in error_message
    assert "found null" in error_message


def test_maybe_str_accepts_valid_values():
    """Test that Maybe[str] accepts valid string values."""

    @strawberry.input
    class UpdateInput:
        name: strawberry.Maybe[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update(self, input: UpdateInput) -> str:
            if input.name is not None:
                return f"Updated to: {input.name.value}"
            return "No change"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with valid string value should work
    query = """
    mutation {
        update(input: { name: "John" })
    }
    """

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data == {"update": "Updated to: John"}


def test_maybe_str_handles_absent_fields():
    """Test that Maybe[str] properly handles absent fields.

    BEHAVIOR:
    - Absent fields are allowed and result in None value
    """

    @strawberry.input
    class UpdateInput:
        name: strawberry.Maybe[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update(self, input: UpdateInput) -> str:
            if input.name is not None:
                return f"Updated to: {input.name.value}"
            return "No change"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with absent field should work and return "No change"
    query = """
    mutation {
        update(input: {})
    }
    """

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data == {"update": "No change"}


def test_maybe_str_error_messages():
    """Test that Maybe[str] provides error messages when null is rejected."""

    @strawberry.input
    class UpdateInput:
        name: strawberry.Maybe[str]  # Rejects null at Python validation level
        phone: strawberry.Maybe[str | None]  # Can accept null

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update(self, input: UpdateInput) -> str:
            return "Updated"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test that null to name field produces a validation error
    query = """
    mutation {
        update(input: { name: null, phone: null })
    }
    """

    result = schema.execute_sync(query)
    assert result.errors
    assert len(result.errors) == 1

    # The error should be related to the name field, not phone field
    error_message = str(result.errors[0])
    # Error message from Python validation
    assert "Expected value of type" in error_message
    assert "found null" in error_message


def test_mixed_maybe_field_behavior():
    """Test schema with both Maybe[T] and Maybe[T | None] behave differently."""

    @strawberry.input
    class UpdateUserInput:
        # Should accept value or absent, reject null
        username: strawberry.Maybe[str]
        # Can accept null, value, or absent
        bio: strawberry.Maybe[str | None]
        # Can accept null, value, or absent
        website: strawberry.Maybe[str | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_user(self, input: UpdateUserInput) -> str:
            result = []

            if input.username is not None:
                result.append(f"username={input.username.value}")
            else:
                result.append("username=unchanged")

            if input.bio is not None:
                bio_value = (
                    input.bio.value if input.bio.value is not None else "cleared"
                )
                result.append(f"bio={bio_value}")
            else:
                result.append("bio=unchanged")

            if input.website is not None:
                website_value = (
                    input.website.value
                    if input.website.value is not None
                    else "cleared"
                )
                result.append(f"website={website_value}")
            else:
                result.append("website=unchanged")

            return ", ".join(result)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test 1: Valid values for all fields
    query1 = """
    mutation {
        updateUser(input: {
            username: "john",
            bio: "Developer",
            website: "example.com"
        })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors
    assert result1.data == {
        "updateUser": "username=john, bio=Developer, website=example.com"
    }

    # Test 2: Null for bio and website should work, but not for username
    query2 = """
    mutation {
        updateUser(input: {
            username: null,
            bio: null,
            website: null
        })
    }
    """
    result2 = schema.execute_sync(query2)
    assert result2.errors  # Should fail due to username: null

    # Test 3: Valid bio/website nulls without username
    query3 = """
    mutation {
        updateUser(input: {
            bio: null,
            website: null
        })
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors
    assert result3.data == {
        "updateUser": "username=unchanged, bio=cleared, website=cleared"
    }

    # Test 4: Absent fields should work
    query4 = """
    mutation {
        updateUser(input: {})
    }
    """
    result4 = schema.execute_sync(query4)
    assert not result4.errors
    assert result4.data == {
        "updateUser": "username=unchanged, bio=unchanged, website=unchanged"
    }


def test_maybe_nested_types():
    """Test Maybe with nested types like lists."""

    @strawberry.input
    class UpdateItemsInput:
        # Cannot accept null list - only valid list or absent
        tags: strawberry.Maybe[list[str]]
        # Can accept null, valid list, or absent
        categories: strawberry.Maybe[list[str] | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_items(self, input: UpdateItemsInput) -> str:
            result = []

            if input.tags is not None:
                result.append(f"tags={input.tags.value}")
            else:
                result.append("tags=unchanged")

            if input.categories is not None:
                cat_value = (
                    input.categories.value
                    if input.categories.value is not None
                    else "cleared"
                )
                result.append(f"categories={cat_value}")
            else:
                result.append("categories=unchanged")

            return ", ".join(result)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test 1: Valid lists for both fields
    query1 = """
    mutation {
        updateItems(input: {
            tags: ["python", "graphql"],
            categories: ["tech", "web"]
        })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors
    assert result1.data == {
        "updateItems": "tags=['python', 'graphql'], categories=['tech', 'web']"
    }

    # Test 2: Null categories should work, but null tags should fail
    query2 = """
    mutation {
        updateItems(input: {
            tags: null,
            categories: null
        })
    }
    """
    result2 = schema.execute_sync(query2)
    assert result2.errors  # Should fail due to tags: null

    # Test 3: Valid categories null without tags
    query3 = """
    mutation {
        updateItems(input: {
            categories: null
        })
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors
    assert result3.data == {"updateItems": "tags=unchanged, categories=cleared"}

    # Test 4: Empty lists should work for both
    query4 = """
    mutation {
        updateItems(input: {
            tags: [],
            categories: []
        })
    }
    """
    result4 = schema.execute_sync(query4)
    assert not result4.errors
    assert result4.data == {"updateItems": "tags=[], categories=[]"}


def test_maybe_resolver_arguments():
    """Test Maybe fields as resolver arguments."""

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self,
            # Cannot accept null - only value or absent
            query: strawberry.Maybe[str] = None,
            # Can accept null, value, or absent
            filter_by: strawberry.Maybe[str | None] = None,
        ) -> str:
            result = []

            if query is not None:
                result.append(f"query={query.value}")
            else:
                result.append("query=unset")

            if filter_by is not None:
                filter_value = (
                    filter_by.value if filter_by.value is not None else "cleared"
                )
                result.append(f"filter={filter_value}")
            else:
                result.append("filter=unset")

            return ", ".join(result)

    schema = strawberry.Schema(query=Query)

    # Test 1: Valid values for both arguments
    query1 = """
    query {
        search(query: "python", filterBy: "category")
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors
    assert result1.data == {"search": "query=python, filter=category"}

    # Test 2: Null filter should work, but null query should fail
    query2 = """
    query {
        search(query: null, filterBy: null)
    }
    """
    result2 = schema.execute_sync(query2)
    assert result2.errors  # Should fail due to query: null

    # Test 3: Valid filter null without query
    query3 = """
    query {
        search(filterBy: null)
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors
    assert result3.data == {"search": "query=unset, filter=cleared"}

    # Test 4: No arguments
    query4 = """
    query {
        search
    }
    """
    result4 = schema.execute_sync(query4)
    assert not result4.errors
    assert result4.data == {"search": "query=unset, filter=unset"}


def test_maybe_graphql_schema_consistency():
    """Test GraphQL schema generation for Maybe types.

    BEHAVIOR:
    - Maybe[str] generates String (optional) - allows absent but rejects null
    - Maybe[str | None] generates String (optional) - allows absent and null
    - Both generate the same GraphQL schema but have different validation
    """

    # Schema with Maybe[str]
    @strawberry.input
    class Input1:
        field: strawberry.Maybe[str]

    @strawberry.type
    class Query1:
        @strawberry.field
        def test(self, input: Input1) -> str:
            return "test"

    schema1 = strawberry.Schema(query=Query1)

    # Schema with Maybe[str | None]
    @strawberry.input
    class Input2:
        field: strawberry.Maybe[str | None]

    @strawberry.type
    class Query2:
        @strawberry.field
        def test(self, input: Input2) -> str:
            return "test"

    schema2 = strawberry.Schema(query=Query2)

    # Document new behavior
    schema1_str = str(schema1)
    schema2_str = str(schema2)

    # Both Maybe[str] and Maybe[str | None] generate String (optional)
    assert "field: String" in schema1_str
    assert "field: String!" not in schema1_str
    assert "field: String" in schema2_str
    assert "field: String!" not in schema2_str


def test_maybe_complex_types():
    """Test Maybe with complex custom types."""

    @strawberry.input
    class AddressInput:
        street: str
        city: str
        zip_code: str | None = None

    @strawberry.input
    class UpdateProfileInput:
        # Cannot accept null address - only valid address or absent
        address: strawberry.Maybe[AddressInput]
        # Can accept null, valid address, or absent
        billing_address: strawberry.Maybe[AddressInput | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_profile(self, input: UpdateProfileInput) -> str:
            result = []

            if input.address is not None:
                addr = input.address.value
                result.append(f"address={addr.street}, {addr.city}")
            else:
                result.append("address=unchanged")

            if input.billing_address is not None:
                if input.billing_address.value is not None:
                    addr = input.billing_address.value
                    result.append(f"billing={addr.street}, {addr.city}")
                else:
                    result.append("billing=cleared")
            else:
                result.append("billing=unchanged")

            return ", ".join(result)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test 1: Valid addresses for both fields
    query1 = """
    mutation {
        updateProfile(input: {
            address: { street: "123 Main", city: "NYC" },
            billingAddress: { street: "456 Oak", city: "LA" }
        })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors
    assert result1.data == {
        "updateProfile": "address=123 Main, NYC, billing=456 Oak, LA"
    }

    # Test 2: Null billing should work, but null address should fail
    query2 = """
    mutation {
        updateProfile(input: {
            address: null,
            billingAddress: null
        })
    }
    """
    result2 = schema.execute_sync(query2)
    assert result2.errors  # Should fail due to address: null

    # Test 3: Valid billing null without address
    query3 = """
    mutation {
        updateProfile(input: {
            billingAddress: null
        })
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors
    assert result3.data == {"updateProfile": "address=unchanged, billing=cleared"}

    # Test 4: Absent fields
    query4 = """
    mutation {
        updateProfile(input: {})
    }
    """
    result4 = schema.execute_sync(query4)
    assert not result4.errors
    assert result4.data == {"updateProfile": "address=unchanged, billing=unchanged"}


def test_maybe_union_with_none_works():
    """Test that Maybe[T | None] works correctly (this should pass)."""

    @strawberry.input
    class TestInput:
        # This should work correctly - can accept value, null, or absent
        field: strawberry.Maybe[str | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            if input.field is not None:
                if input.field.value is not None:
                    return f"value={input.field.value}"
                return "null"
            return "absent"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Schema should show optional field
    schema_str = str(schema)
    assert "field: String" in schema_str
    assert "field: String!" not in schema_str

    # Test valid value
    result1 = schema.execute_sync('mutation { test(input: { field: "hello" }) }')
    assert not result1.errors
    assert result1.data == {"test": "value=hello"}

    # Test null value
    result2 = schema.execute_sync("mutation { test(input: { field: null }) }")
    assert not result2.errors
    assert result2.data == {"test": "null"}

    # Test absent field
    result3 = schema.execute_sync("mutation { test(input: {}) }")
    assert not result3.errors
    assert result3.data == {"test": "absent"}


def test_maybe_behavior_documented():
    """Document the behavior of Maybe[str] vs Maybe[str | None]."""

    @strawberry.input
    class CompareInput:
        # Generates String (optional) but rejects null at Python level
        required_field: strawberry.Maybe[str]
        # Generates String (optional) and accepts null
        optional_field: strawberry.Maybe[str | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def compare(self, input: CompareInput) -> str:
            return "test"

    schema = strawberry.Schema(query=Query)
    schema_str = str(schema)

    # Document behavior - both generate optional fields
    assert "requiredField: String" in schema_str
    assert "requiredField: String!" not in schema_str
    assert "optionalField: String" in schema_str
    assert "optionalField: String!" not in schema_str


def test_maybe_schema_generation():
    """Test schema behavior - both Maybe[T] and Maybe[T | None] generate optional."""

    @strawberry.input
    class Input1:
        field: strawberry.Maybe[str]

    @strawberry.input
    class Input2:
        field: strawberry.Maybe[str | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def test1(self, input: Input1) -> str:
            return "test"

        @strawberry.field
        def test2(self, input: Input2) -> str:
            return "test"

    schema = strawberry.Schema(query=Query)
    schema_str = str(schema)

    # Both Maybe[str] and Maybe[str | None] generate String (optional)
    assert "field: String" in schema_str  # Both Input1 and Input2 have optional fields
    assert "field: String!" not in schema_str  # No required fields


def test_maybe_validation():
    """Test that Maybe[T] rejects null at Python validation time, not GraphQL schema time."""

    @strawberry.input
    class TestInput:
        field: strawberry.Maybe[
            str
        ]  # Should be optional in schema but reject null in validation

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test(self, input: TestInput) -> str:
            return "test"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Schema should show optional field
    schema_str = str(schema)
    assert "field: String" in schema_str
    assert "field: String!" not in schema_str

    # Null should be rejected during Python validation, not GraphQL parsing
    result = schema.execute_sync("mutation { test(input: { field: null }) }")
    assert result.errors
    # Error should be a validation error, not a GraphQL parsing error
    error_message = str(result.errors[0])
    assert "Expected value of type" in error_message
    assert "found null" in error_message


def test_maybe_comprehensive_behavior_comparison():
    """Comprehensive test comparing Maybe[T] vs Maybe[T | None] behavior."""

    @strawberry.input
    class ComprehensiveInput:
        # String (optional) - can be value or absent, but rejects null at Python level
        strict_field: strawberry.Maybe[str]
        # String (optional) - can be null, value, or absent
        flexible_field: strawberry.Maybe[str | None]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def test_comprehensive(self, input: ComprehensiveInput) -> str:
            result = []

            # This logic works for both current and intended behavior
            if input.strict_field is not None:
                result.append(f"strict={input.strict_field.value}")
            else:
                result.append("strict=absent")

            if input.flexible_field is not None:
                if input.flexible_field.value is not None:
                    result.append(f"flexible={input.flexible_field.value}")
                else:
                    result.append("flexible=null")
            else:
                result.append("flexible=absent")

            return ", ".join(result)

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    schema_str = str(schema)

    # Document schema generation - both are optional
    assert "strictField: String" in schema_str
    assert "strictField: String!" not in schema_str
    assert "flexibleField: String" in schema_str
    assert "flexibleField: String!" not in schema_str

    # Test 1: Valid values work for both
    result1 = schema.execute_sync("""
        mutation {
            testComprehensive(input: {
                strictField: "hello",
                flexibleField: "world"
            })
        }
    """)
    assert not result1.errors
    assert result1.data == {"testComprehensive": "strict=hello, flexible=world"}

    # Test 2: Only flexible field can be null
    result2 = schema.execute_sync("""
        mutation {
            testComprehensive(input: {
                strictField: "hello",
                flexibleField: null
            })
        }
    """)
    assert not result2.errors
    assert result2.data == {"testComprehensive": "strict=hello, flexible=null"}

    # Test 3: Strict field null causes Python validation error
    result3 = schema.execute_sync("""
        mutation {
            testComprehensive(input: {
                strictField: null,
                flexibleField: "world"
            })
        }
    """)
    assert result3.errors  # Python validation error - cannot pass null to Maybe[str]

    # Test 4: Both fields can be omitted now
    result4 = schema.execute_sync("""
        mutation {
            testComprehensive(input: {
                strictField: "hello"
            })
        }
    """)
    assert not result4.errors
    assert result4.data == {"testComprehensive": "strict=hello, flexible=absent"}

    # Test 5: Strict field can now be omitted (both fields optional in schema)
    result5 = schema.execute_sync("""
        mutation {
            testComprehensive(input: {
                flexibleField: "world"
            })
        }
    """)
    assert not result5.errors  # No error - both fields are optional in schema
    assert result5.data == {"testComprehensive": "strict=absent, flexible=world"}


def test_maybe_with_explicit_field_description():
    """Handle case where strawberry.field annotation is used on a field with Maybe[T] type."""

    @strawberry.input
    class InputData:
        name: strawberry.Maybe[str | None] = strawberry.field(
            description="This strawberry.field annotation was breaking in default injection"
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, data: InputData) -> str:
            if data.name is None:
                return "I am a test, and I received: None"
            return "I am a test, and I received: " + str(data.name.value)

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        input InputData {
          \"\"\"This strawberry.field annotation was breaking in default injection\"\"\"
          name: String
        }

        type Query {
          test(data: InputData!): String!
        }"""
    )

    query1 = """
    query {
        test(data: { name: null })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors

    query2 = """
    query {
        test(data: { name: "hello" })
    }
    """
    result2 = schema.execute_sync(query2)
    assert not result2.errors

    query3 = """
    query {
        test(data: {})
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors


def test_maybe_wrapped_with_annotated_typing():
    """Handle case where Maybe is wrapped with Annotated typing."""

    @strawberry.input
    class InputData:
        name: Annotated[strawberry.Maybe[str | None], "some meta"]

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, data: InputData) -> str:
            if data.name is None:
                return "I am a test, and I received: None"
            return "I am a test, and I received: " + str(data.name.value)

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        input InputData {
          name: String
        }

        type Query {
          test(data: InputData!): String!
        }"""
    )
    query1 = """
    query {
        test(data: { name: null })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors

    query2 = """
    query {
        test(data: { name: "hello" })
    }
    """
    result2 = schema.execute_sync(query2)
    assert not result2.errors

    query3 = """
    query {
        test(data: {})
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors


def test_maybe_with_annotated_and_explicit_definition():
    """Handle case where Maybe is wrapped with Annotated typing."""

    @strawberry.input
    class InputData:
        name: Annotated[strawberry.Maybe[str | None], "some meta"] = strawberry.field(
            description="This strawberry.field annotation was breaking in default injection"
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, data: InputData) -> str:
            if data.name is None:
                return "I am a test, and I received: None"
            return "I am a test, and I received: " + str(data.name.value)

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        input InputData {
          \"\"\"This strawberry.field annotation was breaking in default injection\"\"\"
          name: String
        }

        type Query {
          test(data: InputData!): String!
        }"""
    )
    query1 = """
    query {
        test(data: { name: null })
    }
    """
    result1 = schema.execute_sync(query1)
    assert not result1.errors

    query2 = """
    query {
        test(data: { name: "hello" })
    }
    """
    result2 = schema.execute_sync(query2)
    assert not result2.errors

    query3 = """
    query {
        test(data: {})
    }
    """
    result3 = schema.execute_sync(query3)
    assert not result3.errors
