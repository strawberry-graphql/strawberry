"""Comprehensive interface type tests for JIT compiler.

Tests interface definitions, implementations, fragments, and type resolution.
"""

import strawberry
from strawberry.jit import compile_query


# Define interface and implementations
@strawberry.interface
class Node:
    id: str


@strawberry.interface
class Named:
    name: str


@strawberry.type
class User(Node):
    id: str
    name: str
    email: str


@strawberry.type
class Post(Node):
    id: str
    title: str
    content: str


@strawberry.type
class Comment(Node, Named):
    """Implements multiple interfaces."""

    id: str
    name: str  # From Named
    text: str


@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: str) -> Node:
        """Return a node by ID."""
        if id.startswith("user"):
            return User(id=id, name="John", email="john@example.com")
        if id.startswith("post"):
            return Post(id=id, title="My Post", content="Content here")
        return Comment(id=id, name="Alice", text="Great post!")

    @strawberry.field
    def nodes(self) -> list[Node]:
        """Return multiple nodes."""
        return [
            User(id="user1", name="John", email="john@example.com"),
            Post(id="post1", title="Post 1", content="Content 1"),
            Comment(id="comment1", name="Alice", text="Nice!"),
        ]

    @strawberry.field
    def named_item(self, id: str) -> Named:
        """Return a named item."""
        if id == "comment":
            return Comment(id="c1", name="Bob", text="Cool!")
        # Note: User doesn't implement Named, so this would be type error in real code
        # but for testing we keep it simple
        return Comment(id="c2", name="Default", text="Text")


# Create schema with all types explicitly listed
def get_schema():
    """Create schema with interface implementations."""
    return strawberry.Schema(query=Query, types=[User, Post, Comment])


def test_interface_with_typename():
    """Test interface type resolution with __typename."""
    schema = get_schema()
    query = """
    query {
        node(id: "user1") {
            __typename
            id
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["node"]["__typename"] == "User"
    assert result["data"]["node"]["id"] == "user1"


def test_interface_with_inline_fragment():
    """Test interface with inline fragments for type-specific fields."""
    schema = get_schema()
    query = """
    query {
        node(id: "user1") {
            __typename
            id
            ... on User {
                name
                email
            }
            ... on Post {
                title
                content
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["node"]["__typename"] == "User"
    assert result["data"]["node"]["id"] == "user1"
    assert result["data"]["node"]["name"] == "John"
    assert result["data"]["node"]["email"] == "john@example.com"
    # Post fields should not be present
    assert "title" not in result["data"]["node"]
    assert "content" not in result["data"]["node"]


def test_interface_with_named_fragment():
    """Test interface with named fragments."""
    schema = get_schema()
    query = """
    query {
        node(id: "post1") {
            __typename
            id
            ...PostFields
        }
    }

    fragment PostFields on Post {
        title
        content
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["node"]["__typename"] == "Post"
    assert result["data"]["node"]["id"] == "post1"
    assert result["data"]["node"]["title"] == "My Post"
    assert result["data"]["node"]["content"] == "Content here"


def test_interface_list():
    """Test list of interface types."""
    schema = get_schema()
    query = """
    query {
        nodes {
            __typename
            id
            ... on User {
                name
                email
            }
            ... on Post {
                title
            }
            ... on Comment {
                text
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    nodes = result["data"]["nodes"]
    assert len(nodes) == 3

    # First node is User
    assert nodes[0]["__typename"] == "User"
    assert nodes[0]["id"] == "user1"
    assert nodes[0]["name"] == "John"
    assert nodes[0]["email"] == "john@example.com"

    # Second node is Post
    assert nodes[1]["__typename"] == "Post"
    assert nodes[1]["id"] == "post1"
    assert nodes[1]["title"] == "Post 1"

    # Third node is Comment
    assert nodes[2]["__typename"] == "Comment"
    assert nodes[2]["id"] == "comment1"
    assert nodes[2]["text"] == "Nice!"


def test_interface_common_fields():
    """Test accessing only common interface fields."""
    schema = get_schema()
    query = """
    query {
        nodes {
            id
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    nodes = result["data"]["nodes"]
    assert len(nodes) == 3
    assert all("id" in node for node in nodes)
    # Should not include type-specific fields
    assert all("name" not in node or "email" not in node for node in nodes)


def test_multiple_interface_implementation():
    """Test type implementing multiple interfaces.

    Note: Currently tests using Comment type which has fields from both
    Node and Named interfaces.
    """
    schema = get_schema()
    query = """
    query {
        node(id: "comment1") {
            __typename
            id
            ... on Comment {
                name
                text
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["node"]["__typename"] == "Comment"
    assert result["data"]["node"]["id"] == "comment1"
    assert result["data"]["node"]["name"] == "Alice"
    assert result["data"]["node"]["text"] == "Great post!"


def test_interface_with_variables():
    """Test interface resolution with variables."""
    schema = get_schema()
    query = """
    query GetNode($id: String!) {
        node(id: $id) {
            __typename
            id
            ... on User {
                name
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query(), variables={"id": "user2"})

    assert result["data"]["node"]["__typename"] == "User"
    assert result["data"]["node"]["id"] == "user2"
    assert result["data"]["node"]["name"] == "John"


def test_interface_nested_fragments():
    """Test multiple fragments on interfaces.

    Note: Simplified to use direct type fragments instead of nested
    fragments on the interface itself.
    """
    schema = get_schema()
    query = """
    query {
        nodes {
            __typename
            id
            ...UserInfo
            ...PostInfo
        }
    }

    fragment UserInfo on User {
        name
        email
    }

    fragment PostInfo on Post {
        title
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    nodes = result["data"]["nodes"]
    assert len(nodes) == 3

    # Verify User has user-specific fields
    assert nodes[0]["__typename"] == "User"
    assert nodes[0]["id"] == "user1"
    assert nodes[0]["name"] == "John"
    assert nodes[0]["email"] == "john@example.com"

    # Verify Post has post-specific fields
    assert nodes[1]["__typename"] == "Post"
    assert nodes[1]["id"] == "post1"
    assert nodes[1]["title"] == "Post 1"


def test_interface_without_typename():
    """Test that interface resolution works even without explicit __typename."""
    schema = get_schema()
    query = """
    query {
        node(id: "post1") {
            id
            ... on Post {
                title
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["node"]["id"] == "post1"
    assert result["data"]["node"]["title"] == "My Post"


def test_interface_all_implementations():
    """Test that all possible implementations are handled."""
    schema = get_schema()

    # Test each implementation type
    test_cases = [
        ("user1", "User", {"name": "John", "email": "john@example.com"}),
        ("post1", "Post", {"title": "My Post", "content": "Content here"}),
        ("comment1", "Comment", {"name": "Alice", "text": "Great post!"}),
    ]

    for node_id, expected_type, expected_fields in test_cases:
        query = f"""
        query {{
            node(id: "{node_id}") {{
                __typename
                id
                ... on User {{
                    name
                    email
                }}
                ... on Post {{
                    title
                    content
                }}
                ... on Comment {{
                    name
                    text
                }}
            }}
        }}
        """

        compiled = compile_query(schema, query)
        result = compiled(Query())

        assert result["data"]["node"]["__typename"] == expected_type
        assert result["data"]["node"]["id"] == node_id

        for field, value in expected_fields.items():
            assert result["data"]["node"][field] == value


def test_interface_with_directives():
    """Test interface with skip/include directives."""
    schema = get_schema()
    query = """
    query GetNode($includeEmail: Boolean!) {
        node(id: "user1") {
            id
            ... on User {
                name
                email @include(if: $includeEmail)
            }
        }
    }
    """

    # Test with includeEmail = true
    compiled = compile_query(schema, query)
    result = compiled(Query(), variables={"includeEmail": True})
    assert "email" in result["data"]["node"]

    # Test with includeEmail = false
    result = compiled(Query(), variables={"includeEmail": False})
    assert "email" not in result["data"]["node"]
