"""Test the native Strawberry type map for fast lookups."""

from typing import Optional

import strawberry


def test_type_map_basic_functionality():
    """Test basic type map operations."""

    @strawberry.type
    class Author:
        id: str
        full_name: str  # Will become fullName in GraphQL
        email_address: str  # Will become emailAddress in GraphQL

        @strawberry.field
        def total_posts(self) -> int:
            """Custom resolver with snake_case name."""
            return 5

    @strawberry.type
    class Post:
        id: str
        title: str
        author_name: str  # Will become authorName in GraphQL
        is_published: bool  # Will become isPublished in GraphQL

    @strawberry.type
    class Query:
        @strawberry.field
        def get_posts(self, author_id: Optional[str] = None) -> list[Post]:
            """Get posts, optionally filtered by author."""
            return []

        @strawberry.field
        def find_author(self, email: str) -> Optional[Author]:
            """Find author by email."""
            return None

    schema = strawberry.Schema(Query)
    type_map = schema.type_map

    # Test type retrieval
    assert type_map.get_type("Query") is not None
    assert type_map.get_type("Author") is not None
    assert type_map.get_type("Post") is not None
    assert type_map.get_type("NonExistent") is None

    # Test field retrieval by GraphQL name
    query_get_posts = type_map.get_field("Query", "getPosts")
    assert query_get_posts is not None
    assert query_get_posts.python_name == "get_posts"
    assert query_get_posts.graphql_name == "getPosts"

    # Test field retrieval by Python name
    query_get_posts_py = type_map.get_field_by_python_name("Query", "get_posts")
    assert query_get_posts_py is query_get_posts  # Same field object

    # Test field name conversion
    assert type_map.convert_field_name("Query", "getPosts") == "get_posts"
    assert type_map.convert_field_name("Query", "findAuthor") == "find_author"

    # Test Author fields
    author_field = type_map.get_field("Author", "fullName")
    assert author_field is not None
    assert author_field.python_name == "full_name"
    assert author_field.graphql_name == "fullName"

    email_field = type_map.get_field("Author", "emailAddress")
    assert email_field is not None
    assert email_field.python_name == "email_address"

    # Test custom resolver field
    total_posts_field = type_map.get_field("Author", "totalPosts")
    assert total_posts_field is not None
    assert total_posts_field.python_name == "total_posts"

    # Test Post fields
    author_name_field = type_map.get_field("Post", "authorName")
    assert author_name_field is not None
    assert author_name_field.python_name == "author_name"

    is_published_field = type_map.get_field("Post", "isPublished")
    assert is_published_field is not None
    assert is_published_field.python_name == "is_published"

    # Test existence checks
    assert type_map.has_type("Query")
    assert type_map.has_type("Author")
    assert not type_map.has_type("NonExistent")

    assert type_map.has_field("Query", "getPosts")
    assert type_map.has_field("Author", "fullName")
    assert not type_map.has_field("Query", "nonExistent")

    # Test root types
    assert type_map.query_type is not None
    assert type_map.mutation_type is None  # No mutations defined
    assert type_map.subscription_type is None  # No subscriptions defined


def test_type_map_async_field_detection():
    """Test that type map correctly identifies async fields."""

    @strawberry.type
    class Query:
        @strawberry.field
        def sync_field(self) -> str:
            return "sync"

        @strawberry.field
        async def async_field(self) -> str:
            return "async"

    schema = strawberry.Schema(Query)
    type_map = schema.type_map

    # Test async field detection
    assert not type_map.is_field_async("Query", "syncField")
    assert type_map.is_field_async("Query", "asyncField")


def test_type_map_field_arguments():
    """Test that type map provides access to field arguments."""

    @strawberry.type
    class Query:
        @strawberry.field
        def search(
            self,
            query: str,
            limit: int = 10,
            offset: Optional[int] = None,
        ) -> list[str]:
            return []

    schema = strawberry.Schema(Query)
    type_map = schema.type_map

    # Get field arguments
    args = type_map.get_field_arguments("Query", "search")
    assert len(args) == 3

    # Arguments should have their Python names
    arg_names = [arg.python_name for arg in args]
    assert "query" in arg_names
    assert "limit" in arg_names
    assert "offset" in arg_names


def test_type_map_with_mutations():
    """Test type map with mutations."""

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, title: str, author_id: str) -> str:
            return "post-id"

        @strawberry.mutation
        async def delete_post(self, post_id: str) -> bool:
            return True

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(Query, mutation=Mutation)
    type_map = schema.type_map

    # Test mutation type
    assert type_map.mutation_type is not None
    assert type_map.get_type("Mutation") is not None

    # Test mutation fields
    create_field = type_map.get_field("Mutation", "createPost")
    assert create_field is not None
    assert create_field.python_name == "create_post"
    assert not type_map.is_field_async("Mutation", "createPost")

    delete_field = type_map.get_field("Mutation", "deletePost")
    assert delete_field is not None
    assert delete_field.python_name == "delete_post"
    assert type_map.is_field_async("Mutation", "deletePost")


def test_field_map_operations():
    """Test the FieldMap class directly."""
    from strawberry.schema.type_map import FieldMap
    from strawberry.types.field import StrawberryField

    field_map = FieldMap()

    # Create mock fields
    field1 = StrawberryField(python_name="author_name", graphql_name=None)
    field2 = StrawberryField(python_name="is_published", graphql_name=None)

    # Add fields with their names
    field_map.add_field("authorName", "author_name", field1)
    field_map.add_field("isPublished", "is_published", field2)

    # Test retrieval by GraphQL name
    assert field_map.get_by_graphql_name("authorName") is field1
    assert field_map.get_by_graphql_name("isPublished") is field2
    assert field_map.get_by_graphql_name("nonExistent") is None

    # Test retrieval by Python name
    assert field_map.get_by_python_name("author_name") is field1
    assert field_map.get_by_python_name("is_published") is field2
    assert field_map.get_by_python_name("non_existent") is None

    # Test name conversions
    assert field_map.get_python_name("authorName") == "author_name"
    assert field_map.get_python_name("isPublished") == "is_published"
    assert field_map.get_graphql_name("author_name") == "authorName"
    assert field_map.get_graphql_name("is_published") == "isPublished"

    # Test that names were set on fields
    assert field1.graphql_name == "authorName"
    assert field1.python_name == "author_name"
    assert field2.graphql_name == "isPublished"
    assert field2.python_name == "is_published"


if __name__ == "__main__":
    test_type_map_basic_functionality()
    test_type_map_async_field_detection()
    test_type_map_field_arguments()
    test_type_map_with_mutations()
    test_field_map_operations()
    print("✅ All type map tests passed!")
