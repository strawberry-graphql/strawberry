"""Test union type support in JIT compiler."""

from typing import Annotated
from typing import Union as PyUnion

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Define union member types
@strawberry.type
class Book:
    __typename: str = "Book"
    title: str
    author: str
    pages: int

    @strawberry.field
    def summary(self) -> str:
        return f"{self.title} by {self.author}"


@strawberry.type
class Movie:
    __typename: str = "Movie"
    title: str
    director: str
    duration: int  # in minutes

    @strawberry.field
    def summary(self) -> str:
        return f"{self.title} directed by {self.director}"


@strawberry.type
class Song:
    __typename: str = "Song"
    title: str
    artist: str
    duration: int  # in seconds

    @strawberry.field
    def album(self) -> str:
        return "Greatest Hits"


# Define union type
MediaItem = Annotated[PyUnion[Book, Movie, Song], strawberry.union("MediaItem")]


@strawberry.type
class Library:
    name: str

    @strawberry.field
    def items(self) -> list[MediaItem]:
        """Return a mixed list of media items."""
        return [
            Book(title="1984", author="George Orwell", pages=328),
            Movie(title="Inception", director="Christopher Nolan", duration=148),
            Song(title="Bohemian Rhapsody", artist="Queen", duration=354),
            Book(title="The Hobbit", author="J.R.R. Tolkien", pages=310),
        ]

    @strawberry.field
    def featured_item(self) -> MediaItem:
        """Return a single media item."""
        return Movie(title="The Matrix", director="Wachowski Sisters", duration=136)

    @strawberry.field
    def random_item(self, item_type: str = "book") -> MediaItem:
        """Return item based on type."""
        if item_type == "movie":
            return Movie(title="Star Wars", director="George Lucas", duration=121)
        if item_type == "song":
            return Song(title="Imagine", artist="John Lennon", duration=183)
        return Book(title="Dune", author="Frank Herbert", pages=688)


@strawberry.type
class Query:
    @strawberry.field
    def library(self) -> Library:
        return Library(name="Central Library")

    @strawberry.field
    def search(self, query: str) -> list[MediaItem]:
        """Search for media items."""
        results = []
        if "book" in query.lower():
            results.append(
                Book(title="Search Result Book", author="Unknown", pages=100)
            )
        if "movie" in query.lower():
            results.append(
                Movie(title="Search Result Movie", director="Unknown", duration=90)
            )
        return results


def test_union_type_resolution():
    """Test basic union type resolution with __typename."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        library {
            featuredItem {
                __typename
                ... on Movie {
                    title
                    director
                    duration
                }
                ... on Book {
                    title
                    author
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())

    assert result.data["library"]["featuredItem"]["__typename"] == "Movie"
    assert result.data["library"]["featuredItem"]["title"] == "The Matrix"
    assert result.data["library"]["featuredItem"]["director"] == "Wachowski Sisters"

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())

    assert jit_result["library"]["featuredItem"]["__typename"] == "Movie"
    assert jit_result["library"]["featuredItem"]["title"] == "The Matrix"
    assert jit_result["library"]["featuredItem"]["director"] == "Wachowski Sisters"

    print("✅ Basic union type resolution works")


def test_union_list_field():
    """Test union types in list fields."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        library {
            items {
                __typename
                ... on Book {
                    title
                    author
                    pages
                }
                ... on Movie {
                    title
                    director
                    duration
                }
                ... on Song {
                    title
                    artist
                    album
                }
            }
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    items = result["library"]["items"]
    assert len(items) == 4

    # Check first item (Book)
    assert items[0]["__typename"] == "Book"
    assert items[0]["title"] == "1984"
    assert items[0]["author"] == "George Orwell"
    assert items[0]["pages"] == 328

    # Check second item (Movie)
    assert items[1]["__typename"] == "Movie"
    assert items[1]["title"] == "Inception"
    assert items[1]["director"] == "Christopher Nolan"
    assert items[1]["duration"] == 148

    # Check third item (Song)
    assert items[2]["__typename"] == "Song"
    assert items[2]["title"] == "Bohemian Rhapsody"
    assert items[2]["artist"] == "Queen"
    assert items[2]["album"] == "Greatest Hits"

    print("✅ Union list fields work")


def test_union_with_fragments():
    """Test union types with named fragments."""
    schema = strawberry.Schema(Query)

    query = """
    fragment BookDetails on Book {
        title
        author
        pages
        summary
    }

    fragment MovieDetails on Movie {
        title
        director
        duration
        summary
    }

    query {
        library {
            featuredItem {
                __typename
                ...BookDetails
                ...MovieDetails
            }
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    item = result["library"]["featuredItem"]
    assert item["__typename"] == "Movie"
    assert item["title"] == "The Matrix"
    assert item["director"] == "Wachowski Sisters"
    assert item["summary"] == "The Matrix directed by Wachowski Sisters"

    print("✅ Union with fragments works")


def test_union_with_arguments():
    """Test union field with arguments."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        library {
            bookItem: randomItem(itemType: "book") {
                __typename
                ... on Book {
                    title
                    author
                }
            }
            movieItem: randomItem(itemType: "movie") {
                __typename
                ... on Movie {
                    title
                    director
                }
            }
            songItem: randomItem(itemType: "song") {
                __typename
                ... on Song {
                    title
                    artist
                }
            }
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    # Check book
    assert result["library"]["bookItem"]["__typename"] == "Book"
    assert result["library"]["bookItem"]["title"] == "Dune"
    assert result["library"]["bookItem"]["author"] == "Frank Herbert"

    # Check movie
    assert result["library"]["movieItem"]["__typename"] == "Movie"
    assert result["library"]["movieItem"]["title"] == "Star Wars"
    assert result["library"]["movieItem"]["director"] == "George Lucas"

    # Check song
    assert result["library"]["songItem"]["__typename"] == "Song"
    assert result["library"]["songItem"]["title"] == "Imagine"
    assert result["library"]["songItem"]["artist"] == "John Lennon"

    print("✅ Union with arguments works")


def test_union_without_typename():
    """Test union resolution without explicit __typename."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        library {
            featuredItem {
                ... on Movie {
                    title
                    director
                }
                ... on Book {
                    title
                    author
                }
            }
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    item = result["library"]["featuredItem"]
    # Should still resolve correctly based on type
    assert item["title"] == "The Matrix"
    assert item["director"] == "Wachowski Sisters"
    assert "author" not in item  # Book fields should not be present

    print("✅ Union without explicit __typename works")


def test_union_search_query():
    """Test union in search results."""
    schema = strawberry.Schema(Query)

    query = """
    query Search($q: String!) {
        search(query: $q) {
            __typename
            ... on Book {
                title
                author
            }
            ... on Movie {
                title
                director
            }
        }
    }
    """

    # JIT execution with variables
    compiled_fn = compile_query(schema, query)

    # Search for both book and movie
    result = compiled_fn(Query(), variables={"q": "book movie"})

    assert len(result["search"]) == 2
    assert result["search"][0]["__typename"] == "Book"
    assert result["search"][1]["__typename"] == "Movie"

    print("✅ Union search with variables works")


def test_union_performance():
    """Compare performance of union resolution."""
    import time

    schema = strawberry.Schema(Query)

    query = """
    query {
        library {
            items {
                __typename
                ... on Book {
                    title
                    author
                    pages
                    summary
                }
                ... on Movie {
                    title
                    director
                    duration
                    summary
                }
                ... on Song {
                    title
                    artist
                    duration
                    album
                }
            }
        }
    }
    """

    root = Query()
    iterations = 100

    # Standard execution
    start = time.perf_counter()
    for _ in range(iterations):
        result = execute_sync(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start

    # JIT execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(iterations):
        result = compiled_fn(root)
    jit_time = time.perf_counter() - start

    speedup = standard_time / jit_time
    print(f"✅ Union performance: {speedup:.2f}x faster with JIT")
    assert speedup > 1.5, "JIT should be at least 1.5x faster for unions"


def test_union_error_handling():
    """Test error handling in union fields."""

    @strawberry.type
    class ErrorBook:
        __typename: str = "ErrorBook"
        title: str

        @strawberry.field
        def author(self) -> str:
            raise Exception("Author not found")

    ErrorMedia = Annotated[PyUnion[ErrorBook, Movie], strawberry.union("ErrorMedia")]

    @strawberry.type
    class ErrorQuery:
        @strawberry.field
        def media(self) -> ErrorMedia:
            return ErrorBook(title="Error Book")

    schema = strawberry.Schema(ErrorQuery)

    query = """
    query {
        media {
            __typename
            ... on ErrorBook {
                title
                author
            }
        }
    }
    """

    # JIT execution
    compiled_fn = compile_query(schema, query)
    result = compiled_fn(ErrorQuery())

    # Should handle errors properly - when a non-nullable field errors,
    # the parent should be null according to GraphQL spec
    assert isinstance(result, dict)
    assert "data" in result
    assert result["data"] is None or result["data"]["media"] is None
    assert "errors" in result
    assert len(result["errors"]) >= 1
    assert any("Author not found" in err["message"] for err in result["errors"])

    print("✅ Union error handling works")


if __name__ == "__main__":
    test_union_type_resolution()
    test_union_list_field()
    test_union_with_fragments()
    test_union_with_arguments()
    test_union_without_typename()
    test_union_search_query()
    test_union_performance()
    test_union_error_handling()

    print("\n✅ All union type tests passed!")
