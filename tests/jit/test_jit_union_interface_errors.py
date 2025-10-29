"""Comprehensive union and interface error tests for JIT compiler.

Tests error handling in:
- Union type resolution with errors
- Interface type resolution with errors
- Errors in type-specific fields
- Type resolution errors
"""

from typing import Annotated, Union as PyUnion

import pytest

import strawberry
from strawberry.jit import compile_query


# ===== UNION ERROR TESTS =====


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class Movie:
    title: str
    director: str


@strawberry.type
class ErrorBook:
    title: str

    @strawberry.field
    def author(self) -> str | None:
        """Nullable field that errors."""
        raise ValueError("Author lookup failed")


@strawberry.type
class ErrorMovie:
    title: str

    @strawberry.field
    def director(self) -> str:
        """Non-nullable field that errors."""
        raise ValueError("Director lookup failed")


Media = Annotated[PyUnion[Book, Movie], strawberry.union("Media")]
ErrorMedia = Annotated[PyUnion[ErrorBook, ErrorMovie], strawberry.union("ErrorMedia")]


@strawberry.type
class Query:
    @strawberry.field
    def media(self) -> Media:
        return Book(title="Book Title", author="Author Name")

    @strawberry.field
    def error_media(self) -> ErrorMedia:
        return ErrorBook(title="Error Book")

    @strawberry.field
    def non_null_error_media(self) -> ErrorMedia:
        return ErrorMovie(title="Error Movie")

    @strawberry.field
    def media_list(self) -> list[Media]:
        return [
            Book(title="Book 1", author="Author 1"),
            Movie(title="Movie 1", director="Director 1"),
        ]

    @strawberry.field
    def error_media_list(self) -> list[ErrorMedia]:
        return [ErrorBook(title="Book 1"), ErrorMovie(title="Movie 1")]


def test_union_nullable_field_error():
    """Test error in nullable field within union type."""
    schema = strawberry.Schema(query=Query)

    query = """
    query {
        errorMedia {
            __typename
            ... on ErrorBook {
                title
                author
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Should have data with null author
    assert result["data"]["errorMedia"]["__typename"] == "ErrorBook"
    assert result["data"]["errorMedia"]["title"] == "Error Book"
    assert result["data"]["errorMedia"]["author"] is None

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Author lookup failed" in result["errors"][0]["message"]


def test_union_non_nullable_field_error():
    """Test error in non-nullable field within union type.

    When a non-nullable field errors, the entire union value should be null.
    """
    schema = strawberry.Schema(query=Query)

    query = """
    query {
        nonNullErrorMedia {
            __typename
            ... on ErrorMovie {
                title
                director
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Non-nullable error propagates to root
    assert result["data"] is None

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Director lookup failed" in result["errors"][0]["message"]


def test_union_list_with_errors():
    """Test union list where one item has non-nullable error.

    When a list item has a non-nullable field error, the error propagates
    and nulls out the entire list (GraphQL spec behavior).
    """
    schema = strawberry.Schema(query=Query)

    query = """
    query {
        errorMediaList {
            __typename
            ... on ErrorBook {
                title
                author
            }
            ... on ErrorMovie {
                title
                director
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Non-nullable error in list item propagates to null the entire list
    assert result["data"] is None

    # Should have 2 errors (nullable author error + non-nullable director error)
    assert "errors" in result
    assert len(result["errors"]) == 2


def test_union_with_multiple_fragments():
    """Test union with errors in multiple fragments."""
    schema = strawberry.Schema(query=Query)

    query = """
    query {
        errorMediaList {
            ... on ErrorBook {
                title
                author
            }
            ... on ErrorMovie {
                title
                director
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Non-nullable error in list item propagates to root
    assert result["data"] is None
    assert "errors" in result
    assert len(result["errors"]) == 2


# ===== INTERFACE ERROR TESTS =====


@strawberry.interface
class Node:
    id: str


@strawberry.type
class User(Node):
    id: str
    name: str


@strawberry.type
class Post(Node):
    id: str
    title: str


@strawberry.type
class ErrorUser(Node):
    id: str

    @strawberry.field
    def name(self) -> str | None:
        """Nullable field that errors."""
        raise ValueError("Name lookup failed")


@strawberry.type
class ErrorPost(Node):
    id: str

    @strawberry.field
    def title(self) -> str:
        """Non-nullable field that errors."""
        raise ValueError("Title lookup failed")


@strawberry.type
class InterfaceQuery:
    @strawberry.field
    def node(self, id: str) -> Node:
        if id.startswith("user"):
            return ErrorUser(id=id)
        return ErrorPost(id=id)

    @strawberry.field
    def nodes(self) -> list[Node]:
        return [ErrorUser(id="user1"), ErrorPost(id="post1")]


def test_interface_nullable_field_error():
    """Test error in nullable field within interface implementation."""
    schema = strawberry.Schema(
        query=InterfaceQuery, types=[User, Post, ErrorUser, ErrorPost]
    )

    query = """
    query {
        node(id: "user1") {
            id
            ... on ErrorUser {
                name
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(InterfaceQuery())

    # Should have data with null name
    assert result["data"]["node"]["id"] == "user1"
    assert result["data"]["node"]["name"] is None

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Name lookup failed" in result["errors"][0]["message"]


def test_interface_non_nullable_field_error():
    """Test error in non-nullable field within interface implementation.

    When a non-nullable field errors, it propagates to root.
    """
    schema = strawberry.Schema(
        query=InterfaceQuery, types=[User, Post, ErrorUser, ErrorPost]
    )

    query = """
    query {
        node(id: "post1") {
            id
            ... on ErrorPost {
                title
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(InterfaceQuery())

    # Non-nullable error propagates to root
    assert result["data"] is None

    # Should have error
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "Title lookup failed" in result["errors"][0]["message"]


def test_interface_list_with_errors():
    """Test interface list where one item has non-nullable error.

    When a list item has a non-nullable field error, the error propagates
    and nulls out the entire list (GraphQL spec behavior).
    """
    schema = strawberry.Schema(
        query=InterfaceQuery, types=[User, Post, ErrorUser, ErrorPost]
    )

    query = """
    query {
        nodes {
            id
            ... on ErrorUser {
                name
            }
            ... on ErrorPost {
                title
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(InterfaceQuery())

    # Non-nullable error in list item propagates to root
    assert result["data"] is None

    # Should have 2 errors (nullable name error + non-nullable title error)
    assert "errors" in result
    assert len(result["errors"]) == 2


def test_interface_common_fields_with_specific_error():
    """Test accessing common interface fields when type-specific field errors."""
    schema = strawberry.Schema(
        query=InterfaceQuery, types=[User, Post, ErrorUser, ErrorPost]
    )

    query = """
    query {
        nodes {
            id
            __typename
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(InterfaceQuery())

    # Common fields should work even if type-specific fields would error
    assert result["data"]["nodes"][0]["id"] == "user1"
    assert result["data"]["nodes"][0]["__typename"] == "ErrorUser"
    assert result["data"]["nodes"][1]["id"] == "post1"
    assert result["data"]["nodes"][1]["__typename"] == "ErrorPost"

    # No errors since we didn't query the error fields
    assert "errors" not in result


# ===== MIXED SCENARIOS =====


@strawberry.type
class SearchResult:
    """Union-like pattern with interfaces."""

    pass


def test_nested_union_interface_errors():
    """Test errors in nested structures with unions and interfaces."""

    @strawberry.type
    class Container:
        @strawberry.field
        def media(self) -> ErrorMedia:
            return ErrorBook(title="Nested Book")

    @strawberry.type
    class NestedQuery:
        @strawberry.field
        def container(self) -> Container:
            return Container()

    schema = strawberry.Schema(query=NestedQuery)

    query = """
    query {
        container {
            media {
                __typename
                ... on ErrorBook {
                    title
                    author
                }
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(NestedQuery())

    # Should handle nested errors
    assert result["data"]["container"]["media"]["title"] == "Nested Book"
    assert result["data"]["container"]["media"]["author"] is None
    assert "errors" in result


def test_parallel_union_queries():
    """Test multiple union queries with nullable errors."""
    schema = strawberry.Schema(query=Query)

    query = """
    query {
        media1: errorMedia {
            ... on ErrorBook {
                title
                author
            }
        }
        media2: errorMedia {
            ... on ErrorBook {
                title
                author
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    # Both should have partial data (nullable errors)
    assert result["data"]["media1"]["title"] == "Error Book"
    assert result["data"]["media1"]["author"] is None
    assert result["data"]["media2"]["title"] == "Error Book"
    assert result["data"]["media2"]["author"] is None

    # Should have at least 1 error (may share resolver instances)
    assert "errors" in result
    assert len(result["errors"]) >= 1
