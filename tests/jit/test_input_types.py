"""Test input type support in JIT compiler."""

from typing import List, Optional

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Define input types
@strawberry.input
class AddressInput:
    street: str
    city: str
    country: str
    zip_code: Optional[str] = None


@strawberry.input
class PersonInput:
    name: str
    age: int
    email: Optional[str] = None
    address: Optional[AddressInput] = None
    tags: Optional[List[str]] = None


@strawberry.input
class SearchInput:
    query: str
    limit: int = 10
    offset: int = 0
    filters: Optional[List[str]] = None


@strawberry.input
class UpdatePersonInput:
    id: str
    name: Optional[str] = strawberry.UNSET
    age: Optional[int] = strawberry.UNSET
    email: Optional[str] = strawberry.UNSET
    address: Optional[AddressInput] = strawberry.UNSET


# Output types
@strawberry.type
class Address:
    street: str
    city: str
    country: str
    zip_code: Optional[str]


@strawberry.type
class Person:
    id: str
    name: str
    age: int
    email: Optional[str]
    address: Optional[Address]
    tags: List[str]


@strawberry.type
class SearchResult:
    items: List[Person]
    total: int
    has_more: bool


@strawberry.type
class Query:
    @strawberry.field
    def person(self, id: str) -> Optional[Person]:
        """Get a person by ID."""
        if id == "1":
            return Person(
                id="1",
                name="John Doe",
                age=30,
                email="john@example.com",
                address=Address(
                    street="123 Main St",
                    city="New York",
                    country="USA",
                    zip_code="10001",
                ),
                tags=["developer", "python"],
            )
        return None

    @strawberry.field
    def search(self, input: SearchInput) -> SearchResult:
        """Search for people."""
        # Mock search implementation
        items = []
        if "john" in input.query.lower():
            items.append(
                Person(
                    id="1",
                    name="John Doe",
                    age=30,
                    email="john@example.com",
                    address=None,
                    tags=[],
                )
            )

        return SearchResult(
            items=items[: input.limit],
            total=len(items),
            has_more=len(items) > input.limit,
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_person(self, input: PersonInput) -> Person:
        """Create a new person."""
        address = None
        if input.address:
            address = Address(
                street=input.address.street,
                city=input.address.city,
                country=input.address.country,
                zip_code=input.address.zip_code,
            )

        return Person(
            id="new-id",
            name=input.name,
            age=input.age,
            email=input.email,
            address=address,
            tags=input.tags or [],
        )

    @strawberry.mutation
    def update_person(self, input: UpdatePersonInput) -> Optional[Person]:
        """Update an existing person."""
        if input.id != "1":
            return None

        # Mock update - just return updated person
        person = Person(
            id=input.id,
            name=input.name if input.name is not strawberry.UNSET else "John Doe",
            age=input.age if input.age is not strawberry.UNSET else 30,
            email=input.email
            if input.email is not strawberry.UNSET
            else "john@example.com",
            address=None,
            tags=[],
        )

        if input.address is not strawberry.UNSET and input.address:
            person.address = Address(
                street=input.address.street,
                city=input.address.city,
                country=input.address.country,
                zip_code=input.address.zip_code,
            )

        return person


def test_simple_input():
    """Test simple input argument."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    query GetPerson($id: String!) {
        person(id: $id) {
            id
            name
            age
        }
    }
    """

    # Standard execution
    result = execute_sync(
        schema._schema, parse(query), root_value=Query(), variable_values={"id": "1"}
    )

    assert result.data["person"]["id"] == "1"
    assert result.data["person"]["name"] == "John Doe"
    assert result.data["person"]["age"] == 30

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query(), variables={"id": "1"})

    assert jit_result["data"]["person"]["id"] == "1"
    assert jit_result["data"]["person"]["name"] == "John Doe"
    assert jit_result["data"]["person"]["age"] == 30

    print("✅ Simple input works")


def test_input_object():
    """Test input object type."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    query Search($input: SearchInput!) {
        search(input: $input) {
            items {
                id
                name
            }
            total
            hasMore
        }
    }
    """

    variables = {"input": {"query": "John", "limit": 5, "offset": 0}}

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query(), variables=variables)

    assert len(result["data"]["search"]["items"]) == 1
    assert result["data"]["search"]["items"][0]["name"] == "John Doe"
    assert result["data"]["search"]["total"] == 1
    assert result["data"]["search"]["hasMore"] is False

    print("✅ Input object works")


def test_nested_input():
    """Test nested input objects."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreatePerson($input: PersonInput!) {
        createPerson(input: $input) {
            id
            name
            age
            email
            address {
                street
                city
                country
                zipCode
            }
            tags
        }
    }
    """

    variables = {
        "input": {
            "name": "Jane Smith",
            "age": 25,
            "email": "jane@example.com",
            "address": {
                "street": "456 Oak Ave",
                "city": "San Francisco",
                "country": "USA",
                "zipCode": "94102",
            },
            "tags": ["designer", "ui/ux"],
        }
    }

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["data"]["createPerson"]["name"] == "Jane Smith"
    assert result["data"]["createPerson"]["age"] == 25
    assert result["data"]["createPerson"]["email"] == "jane@example.com"
    assert result["data"]["createPerson"]["address"]["street"] == "456 Oak Ave"
    assert result["data"]["createPerson"]["address"]["city"] == "San Francisco"
    assert result["data"]["createPerson"]["tags"] == ["designer", "ui/ux"]

    print("✅ Nested input works")


def test_input_with_defaults():
    """Test input fields with default values."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    query Search($query: String!) {
        search(input: {query: $query}) {
            items {
                name
            }
            total
        }
    }
    """

    # JIT execution - should use default limit and offset
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query(), variables={"query": "John"})

    assert len(result["data"]["search"]["items"]) == 1
    assert result["data"]["search"]["total"] == 1

    print("✅ Input with defaults works")


def test_optional_input_fields():
    """Test optional input fields and UNSET."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation UpdatePerson($input: UpdatePersonInput!) {
        updatePerson(input: $input) {
            id
            name
            age
            email
        }
    }
    """

    # Update only name
    variables = {"input": {"id": "1", "name": "John Updated"}}

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["data"]["updatePerson"]["id"] == "1"
    assert result["data"]["updatePerson"]["name"] == "John Updated"
    assert result["data"]["updatePerson"]["age"] == 30  # Should keep original
    assert (
        result["data"]["updatePerson"]["email"] == "john@example.com"
    )  # Should keep original

    print("✅ Optional input fields work")


def test_list_input():
    """Test list input fields."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreatePerson($name: String!, $age: Int!, $tags: [String!]) {
        createPerson(input: {name: $name, age: $age, tags: $tags}) {
            name
            tags
        }
    }
    """

    variables = {"name": "Bob", "age": 35, "tags": ["manager", "agile", "scrum"]}

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Mutation(), variables=variables)

    assert result["data"]["createPerson"]["name"] == "Bob"
    assert result["data"]["createPerson"]["tags"] == ["manager", "agile", "scrum"]

    print("✅ List input works")


def test_inline_input_object():
    """Test inline input object in query."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    query {
        search(input: {query: "John", limit: 2, offset: 0}) {
            items {
                name
            }
            total
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    assert len(result["data"]["search"]["items"]) == 1
    assert result["data"]["search"]["items"][0]["name"] == "John Doe"

    print("✅ Inline input object works")


def test_input_performance():
    """Compare performance of input handling."""
    import time

    schema = strawberry.Schema(Query, Mutation)

    query = """
    mutation CreateMany($input: PersonInput!) {
        createPerson(input: $input) {
            id
            name
            age
            email
            address {
                street
                city
            }
        }
    }
    """

    variables = {
        "input": {
            "name": "Test User",
            "age": 30,
            "email": "test@example.com",
            "address": {
                "street": "Test St",
                "city": "Test City",
                "country": "Test Country",
            },
        }
    }

    root = Mutation()
    iterations = 100

    # Standard execution
    start = time.perf_counter()
    for _ in range(iterations):
        result = execute_sync(
            schema._schema, parse(query), root_value=root, variable_values=variables
        )
    standard_time = time.perf_counter() - start

    # JIT execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(iterations):
        result = compiled_fn(root, variables=variables)
    jit_time = time.perf_counter() - start

    speedup = standard_time / jit_time
    print(f"✅ Input performance: {speedup:.2f}x faster with JIT")
    assert speedup > 1.5, "JIT should be at least 1.5x faster for inputs"


if __name__ == "__main__":
    test_simple_input()
    test_input_object()
    test_nested_input()
    test_input_with_defaults()
    test_optional_input_fields()
    test_list_input()
    test_inline_input_object()
    test_input_performance()

    print("\n✅ All input type tests passed!")
