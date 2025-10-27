"""Test introspection query support in JIT compiler."""

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query
from tests.jit.conftest import assert_jit_results_match


@strawberry.type
class Author:
    id: str
    name: str
    age: int
    books: list["Book"]


@strawberry.type
class Book:
    id: str
    title: str
    author: Author
    year: int


@strawberry.type
class Query:
    @strawberry.field
    def author(self, id: str) -> Author:
        return Author(
            id=id,
            name="Test Author",
            age=30,
            books=[
                Book(id="1", title="Book 1", author=None, year=2020),
                Book(id="2", title="Book 2", author=None, year=2021),
            ],
        )

    @strawberry.field
    def books(self) -> list[Book]:
        author = Author(id="1", name="Author 1", age=30, books=[])
        return [
            Book(id="1", title="Book 1", author=author, year=2020),
            Book(id="2", title="Book 2", author=author, year=2021),
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_author(self, name: str) -> Author:
        return Author(id="new", name=name, age=25, books=[])


def test_schema_introspection():
    """Test __schema introspection query."""
    schema = strawberry.Schema(Query, Mutation)

    query = """
    {
        __schema {
            queryType {
                name
            }
            mutationType {
                name
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "__schema": {
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"},
        }
    }

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    assert jit_result["data"] == {
        "__schema": {
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"},
        }
    }

    print("✅ __schema introspection works")


def test_type_introspection():
    """Test __type introspection query."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __type(name: "Query") {
            name
            kind
            fields {
                name
                type {
                    name
                    kind
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Compare results
    assert jit_result["data"]["__type"]["name"] == standard_data["__type"]["name"]
    assert jit_result["data"]["__type"]["kind"] == standard_data["__type"]["kind"]
    assert len(jit_result["data"]["__type"]["fields"]) == len(
        standard_data["__type"]["fields"]
    )

    # Check fields
    jit_fields = {f["name"]: f for f in jit_result["data"]["__type"]["fields"]}
    standard_fields = {f["name"]: f for f in standard_data["__type"]["fields"]}
    assert set(jit_fields.keys()) == set(standard_fields.keys())

    print("✅ __type introspection works")


def test_type_kind_introspection():
    """Test type kind introspection."""
    schema = strawberry.Schema(Query)

    query = """
    {
        queryType: __type(name: "Query") {
            name
            kind
        }
        stringType: __type(name: "String") {
            name
            kind
        }
        authorType: __type(name: "Author") {
            name
            kind
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Compare results
    assert_jit_results_match(jit_result, result)

    print("✅ Type kind introspection works")


def test_field_introspection():
    """Test field introspection with arguments."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __type(name: "Query") {
            fields {
                name
                args {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Find author field in both results
    jit_fields = {f["name"]: f for f in jit_result["data"]["__type"]["fields"]}
    standard_fields = {f["name"]: f for f in standard_data["__type"]["fields"]}

    # Check author field has id argument
    assert "author" in jit_fields
    assert "author" in standard_fields
    assert len(jit_fields["author"]["args"]) == len(standard_fields["author"]["args"])

    print("✅ Field introspection with arguments works")


def test_all_types_introspection():
    """Test getting all types from schema."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __schema {
            types {
                name
                kind
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Compare number of types
    assert len(jit_result["data"]["__schema"]["types"]) == len(
        standard_data["__schema"]["types"]
    )

    # Check key types are present
    jit_type_names = {t["name"] for t in jit_result["data"]["__schema"]["types"]}
    standard_type_names = {t["name"] for t in standard_data["__schema"]["types"]}

    assert "Query" in jit_type_names
    assert "Author" in jit_type_names
    assert "Book" in jit_type_names
    assert "String" in jit_type_names
    assert "Int" in jit_type_names

    # Types should match
    assert jit_type_names == standard_type_names

    print("✅ All types introspection works")


def test_nested_type_introspection():
    """Test nested type introspection."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __type(name: "Book") {
            name
            fields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Find author field
    jit_fields = {f["name"]: f for f in jit_result["data"]["__type"]["fields"]}
    standard_fields = {f["name"]: f for f in standard_data["__type"]["fields"]}

    # Check author field type
    assert "author" in jit_fields
    assert (
        jit_fields["author"]["type"]["name"]
        == standard_fields["author"]["type"]["name"]
    )
    assert (
        jit_fields["author"]["type"]["kind"]
        == standard_fields["author"]["type"]["kind"]
    )

    print("✅ Nested type introspection works")


def test_directives_introspection():
    """Test directives introspection."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __schema {
            directives {
                name
                locations
                args {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Check directives
    jit_directives = {
        d["name"]: d for d in jit_result["data"]["__schema"]["directives"]
    }
    standard_directives = {
        d["name"]: d for d in standard_data["__schema"]["directives"]
    }

    # Common directives should be present
    assert "skip" in jit_directives
    assert "include" in jit_directives

    # Check skip directive
    assert set(jit_directives["skip"]["locations"]) == set(
        standard_directives["skip"]["locations"]
    )
    assert len(jit_directives["skip"]["args"]) == len(
        standard_directives["skip"]["args"]
    )

    print("✅ Directives introspection works")


def test_list_type_introspection():
    """Test list type introspection."""
    schema = strawberry.Schema(Query)

    query = """
    {
        __type(name: "Query") {
            fields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Find books field (which returns [Book!]!)
    jit_fields = {f["name"]: f for f in jit_result["data"]["__type"]["fields"]}
    standard_fields = {f["name"]: f for f in standard_data["__type"]["fields"]}

    # Check books field type structure
    assert "books" in jit_fields
    jit_books = jit_fields["books"]["type"]
    standard_books = standard_fields["books"]["type"]

    # Should be NON_NULL -> LIST -> NON_NULL -> Book
    assert jit_books["kind"] == standard_books["kind"]  # NON_NULL
    assert jit_books["ofType"]["kind"] == standard_books["ofType"]["kind"]  # LIST
    assert (
        jit_books["ofType"]["ofType"]["kind"]
        == standard_books["ofType"]["ofType"]["kind"]
    )  # NON_NULL
    # Check if the innermost type has an ofType (it should for Book type)
    if "ofType" in jit_books["ofType"]["ofType"]:
        assert (
            jit_books["ofType"]["ofType"]["ofType"]["name"]
            == standard_books["ofType"]["ofType"]["ofType"]["name"]
        )  # Book

    print("✅ List type introspection works")


def test_introspection_with_variables():
    """Test introspection with variables."""
    schema = strawberry.Schema(Query)

    query = """
    query GetType($typeName: String!) {
        __type(name: $typeName) {
            name
            kind
            fields {
                name
            }
        }
    }
    """

    variables = {"typeName": "Author"}

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None, variables=variables)

    # Compare results
    assert jit_result["data"]["__type"]["name"] == "Author"
    assert jit_result["data"]["__type"]["name"] == standard_data["__type"]["name"]
    assert jit_result["data"]["__type"]["kind"] == standard_data["__type"]["kind"]
    assert len(jit_result["data"]["__type"]["fields"]) == len(
        standard_data["__type"]["fields"]
    )

    print("✅ Introspection with variables works")


def test_graphiql_introspection_query():
    """Test a typical GraphiQL introspection query."""
    schema = strawberry.Schema(Query)

    # Simplified version of GraphiQL's introspection query
    query = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
                ...FullType
            }
        }
    }

    fragment FullType on __Type {
        kind
        name
        description
        fields(includeDeprecated: true) {
            name
            description
            args {
                ...InputValue
            }
            type {
                ...TypeRef
            }
            isDeprecated
            deprecationReason
        }
        inputFields {
            ...InputValue
        }
        interfaces {
            ...TypeRef
        }
        enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
        }
        possibleTypes {
            ...TypeRef
        }
    }

    fragment InputValue on __InputValue {
        name
        description
        type { ...TypeRef }
        defaultValue
    }

    fragment TypeRef on __Type {
        kind
        name
        ofType {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.errors is None
    standard_data = result.data

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(None)

    # Basic checks
    assert "data" in jit_result
    assert "__schema" in jit_result["data"]
    assert jit_result["data"]["__schema"]["queryType"]["name"] == "Query"
    assert "types" in jit_result["data"]["__schema"]
    assert len(jit_result["data"]["__schema"]["types"]) == len(
        standard_data["__schema"]["types"]
    )

    # Check that key types are present with correct structure
    jit_types = {
        t["name"]: t for t in jit_result["data"]["__schema"]["types"] if t.get("name")
    }
    standard_types = {
        t["name"]: t for t in standard_data["__schema"]["types"] if t.get("name")
    }

    # Check Query type
    assert "Query" in jit_types
    assert jit_types["Query"]["kind"] == standard_types["Query"]["kind"]
    assert len(jit_types["Query"]["fields"]) == len(standard_types["Query"]["fields"])

    print("✅ GraphiQL introspection query works")


if __name__ == "__main__":
    test_schema_introspection()
    test_type_introspection()
    test_type_kind_introspection()
    test_field_introspection()
    test_all_types_introspection()
    test_nested_type_introspection()
    test_directives_introspection()
    test_list_type_introspection()
    test_introspection_with_variables()
    test_graphiql_introspection_query()

    print("\n✅ All introspection tests passed!")
