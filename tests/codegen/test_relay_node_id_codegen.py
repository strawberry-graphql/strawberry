from pathlib import Path

import pytest
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.codegen import QueryCodegen, QueryCodegenPlugin
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.codegen.plugins.typescript import TypeScriptPlugin
from strawberry.relay import Node, NodeID


# Create Node types with NodeID
@strawberry.type
class User(Node):
    id: NodeID[str]
    name: str
    email: str | None = None


@strawberry.type
class Post(Node):
    id: NodeID[str]
    title: str
    author: User


@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: strawberry.ID) -> User:
        """Single node query with variable support."""
        return User(id="user-1", name="John Doe")  # pragma: no cover

    @strawberry.field
    def users(self) -> list[User]:
        """List of nodes."""
        return []  # pragma: no cover

    @strawberry.field
    def post(self) -> Post:
        """Nested node types."""
        return Post(  # pragma: no cover
            id="post-1", title="Hello", author=User(id="user-1", name="John Doe")
        )


@pytest.fixture
def relay_schema() -> strawberry.Schema:
    return strawberry.Schema(query=Query)


HERE = Path(__file__).parent
RELAY_QUERIES = list((HERE / "relay_queries").glob("*.graphql"))


@pytest.mark.parametrize(
    ("plugin_class", "plugin_name", "extension"),
    [
        (PythonPlugin, "python", "py"),
        (TypeScriptPlugin, "typescript", "ts"),
    ],
    ids=["python", "typescript"],
)
@pytest.mark.parametrize("query", RELAY_QUERIES, ids=[x.name for x in RELAY_QUERIES])
def test_relay_codegen(
    query: Path,
    plugin_class: type[QueryCodegenPlugin],
    plugin_name: str,
    extension: str,
    snapshot: Snapshot,
    relay_schema: strawberry.Schema,
):
    generator = QueryCodegen(relay_schema, plugins=[plugin_class(query)])

    result = generator.run(query.read_text())

    code = result.to_string()

    snapshot.snapshot_dir = HERE / "snapshots" / "relay" / plugin_name
    snapshot.assert_match(code, f"{query.with_suffix('').stem}.{extension}")
