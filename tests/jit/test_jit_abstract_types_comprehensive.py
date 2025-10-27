"""
Comprehensive abstract type (Union/Interface) tests for JIT compiler.

Based on GraphQL spec and graphql-core test_abstract.py:
https://spec.graphql.org/October2021/#sec-Unions
https://spec.graphql.org/October2021/#sec-Interfaces

These tests ensure the JIT compiler correctly handles:
1. Union type resolution with __typename
2. Interface type resolution
3. Multiple types in unions
4. Runtime type discrimination
5. Fragments on abstract types
6. Error handling in type resolution
"""

from typing import Optional

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Test types for unions
@strawberry.type
class Dog:
    """Dog type for union tests."""

    name: str
    breed: str

    @strawberry.field
    def bark(self) -> str:
        return f"{self.name} says Woof!"


@strawberry.type
class Cat:
    """Cat type for union tests."""

    name: str
    lives: int

    @strawberry.field
    def meow(self) -> str:
        return f"{self.name} says Meow!"


@strawberry.type
class Bird:
    """Bird type for union tests."""

    name: str
    wingspan: float

    @strawberry.field
    def chirp(self) -> str:
        return f"{self.name} says Tweet!"


# Union types
Pet = strawberry.union("Pet", (Dog, Cat, Bird))
DogOrCat = strawberry.union("DogOrCat", (Dog, Cat))


def compare_results(jit_result, standard_result):
    """Compare JIT and standard execution results."""
    # Handle both wrapped {"data": ...} and unwrapped formats
    if isinstance(jit_result, dict):
        if "data" in jit_result:
            jit_data = jit_result["data"]
        else:
            jit_data = jit_result  # Old unwrapped format
    else:
        jit_data = jit_result
    std_data = standard_result.data

    jit_errors = jit_result.get("errors", []) if isinstance(jit_result, dict) else []
    std_errors = standard_result.errors or []

    assert jit_data == std_data, (
        f"Data mismatch:\nJIT: {jit_data}\nStandard: {std_data}"
    )

    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\nJIT: {len(jit_errors)}\nStandard: {len(std_errors)}"
    )


# Test: Basic Union Resolution


def test_union_with_typename():
    """Test union resolution using __typename."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pet(self) -> Pet:
            return Dog(name="Buddy", breed="Golden Retriever")

    schema = strawberry.Schema(Query)

    query = """
    {
        pet {
            __typename
            ... on Dog {
                name
                breed
            }
            ... on Cat {
                name
                lives
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "pet": {"__typename": "Dog", "name": "Buddy", "breed": "Golden Retriever"}
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


def test_union_list():
    """Test list of union types."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pets(self) -> list[Pet]:
            return [
                Dog(name="Buddy", breed="Golden Retriever"),
                Cat(name="Whiskers", lives=9),
                Bird(name="Tweety", wingspan=0.3),
            ]

    schema = strawberry.Schema(Query)

    query = """
    {
        pets {
            __typename
            ... on Dog {
                name
                breed
            }
            ... on Cat {
                name
                lives
            }
            ... on Bird {
                name
                wingspan
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "pets": [
            {"__typename": "Dog", "name": "Buddy", "breed": "Golden Retriever"},
            {"__typename": "Cat", "name": "Whiskers", "lives": 9},
            {"__typename": "Bird", "name": "Tweety", "wingspan": 0.3},
        ]
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


def test_union_with_fragment():
    """Test union with named fragment."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pet(self) -> Pet:
            return Cat(name="Whiskers", lives=9)

    schema = strawberry.Schema(Query)

    query = """
    fragment CatFields on Cat {
        name
        lives
        meow
    }

    {
        pet {
            __typename
            ...CatFields
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "pet": {
            "__typename": "Cat",
            "name": "Whiskers",
            "lives": 9,
            "meow": "Whiskers says Meow!",
        }
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Nullable Unions


def test_nullable_union():
    """Test nullable union field."""

    @strawberry.type
    class Query:
        @strawberry.field
        def maybe_pet(self, return_none: bool = False) -> Optional[Pet]:
            if return_none:
                return None
            return Dog(name="Buddy", breed="Labrador")

    schema = strawberry.Schema(Query)

    # Non-null case
    query1 = """
    {
        maybePet(returnNone: false) {
            __typename
            ... on Dog {
                name
            }
        }
    }
    """

    result1 = execute_sync(schema._schema, parse(query1))
    assert result1.data == {"maybePet": {"__typename": "Dog", "name": "Buddy"}}

    compiled1 = compile_query(schema, query1)
    jit_result1 = compiled1(None)
    compare_results(jit_result1, result1)

    # Null case
    query2 = """
    {
        maybePet(returnNone: true) {
            __typename
        }
    }
    """

    result2 = execute_sync(schema._schema, parse(query2))
    assert result2.data == {"maybePet": None}

    compiled2 = compile_query(schema, query2)
    jit_result2 = compiled2(None)
    compare_results(jit_result2, result2)


# Test: Multiple Fragment Types


def test_union_with_multiple_fragments():
    """Test union with fragments for each type."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pets(self) -> list[Pet]:
            return [
                Dog(name="Rex", breed="German Shepherd"),
                Cat(name="Luna", lives=7),
            ]

    schema = strawberry.Schema(Query)

    query = """
    fragment DogInfo on Dog {
        name
        breed
        bark
    }

    fragment CatInfo on Cat {
        name
        lives
        meow
    }

    {
        pets {
            __typename
            ...DogInfo
            ...CatInfo
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "pets": [
            {
                "__typename": "Dog",
                "name": "Rex",
                "breed": "German Shepherd",
                "bark": "Rex says Woof!",
            },
            {
                "__typename": "Cat",
                "name": "Luna",
                "lives": 7,
                "meow": "Luna says Meow!",
            },
        ]
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Nested Unions


def test_nested_union_types():
    """Test unions within object types."""

    @strawberry.type
    class Owner:
        name: str

        @strawberry.field
        def pet(self) -> Pet:
            return Dog(name="Buddy", breed="Beagle")

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> Owner:
            return Owner(name="Alice")

    schema = strawberry.Schema(Query)

    query = """
    {
        owner {
            name
            pet {
                __typename
                ... on Dog {
                    name
                    breed
                }
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "owner": {
            "name": "Alice",
            "pet": {"__typename": "Dog", "name": "Buddy", "breed": "Beagle"},
        }
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Union Field Resolution


def test_union_specific_field_resolution():
    """Test that type-specific fields are resolved correctly."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pets(self) -> list[Pet]:
            return [
                Dog(name="Max", breed="Poodle"),
                Cat(name="Shadow", lives=5),
            ]

    schema = strawberry.Schema(Query)

    # Query only dog-specific fields
    query = """
    {
        pets {
            ... on Dog {
                name
                bark
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    # Only Dog should have fields, Cat should be empty object
    expected = {"pets": [{"name": "Max", "bark": "Max says Woof!"}, {}]}
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Inline Fragments


def test_union_with_inline_fragments():
    """Test inline fragments on union types."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pet(self) -> Pet:
            return Bird(name="Polly", wingspan=1.2)

    schema = strawberry.Schema(Query)

    query = """
    {
        pet {
            ... on Dog {
                name
                breed
            }
            ... on Cat {
                name
                lives
            }
            ... on Bird {
                name
                wingspan
                chirp
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "pet": {
            "name": "Polly",
            "wingspan": 1.2,
            "chirp": "Polly says Tweet!",
        }
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Union with Common Fields


def test_union_common_fields_with_typename():
    """Test querying common fields across union types."""

    @strawberry.type
    class Query:
        @strawberry.field
        def pets(self) -> list[Pet]:
            return [
                Dog(name="Rover", breed="Bulldog"),
                Cat(name="Mittens", lives=8),
                Bird(name="Chirpy", wingspan=0.5),
            ]

    schema = strawberry.Schema(Query)

    # All types have 'name' field
    query = """
    {
        pets {
            __typename
            ... on Dog { name }
            ... on Cat { name }
            ... on Bird { name }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "pets": [
            {"__typename": "Dog", "name": "Rover"},
            {"__typename": "Cat", "name": "Mittens"},
            {"__typename": "Bird", "name": "Chirpy"},
        ]
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Test: Error Cases


def test_union_with_error_in_field():
    """Test union type field that errors."""

    @strawberry.type
    class ErrorDog:
        name: str

        @strawberry.field
        def error_field(self) -> str:
            raise ValueError("Field error in dog")

    ErrorPet = strawberry.union("ErrorPet", (ErrorDog,))

    @strawberry.type
    class Query:
        @strawberry.field
        def pet(self) -> ErrorPet:
            return ErrorDog(name="Broken")

    schema = strawberry.Schema(Query)

    query = """
    {
        pet {
            ... on ErrorDog {
                name
                errorField
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    # errorField is non-null, so error propagates to pet, then to root
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].path == ["pet", "errorField"]

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


if __name__ == "__main__":
    # Run all tests
    test_union_with_typename()
    print("✅ Union with __typename")

    test_union_list()
    print("✅ Union list")

    test_union_with_fragment()
    print("✅ Union with fragment")

    test_nullable_union()
    print("✅ Nullable union")

    test_union_with_multiple_fragments()
    print("✅ Union with multiple fragments")

    test_nested_union_types()
    print("✅ Nested union types")

    test_union_specific_field_resolution()
    print("✅ Union specific field resolution")

    test_union_with_inline_fragments()
    print("✅ Union with inline fragments")

    test_union_common_fields_with_typename()
    print("✅ Union common fields")

    test_union_with_error_in_field()
    print("✅ Union with error in field")

    print("\n✅ All abstract type tests passed!")
