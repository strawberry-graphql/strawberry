import pytest
from pathlib import Path

from strawberry.codegen import QueryCodegen
from strawberry.codegen.plugins.python import PythonPlugin
from strawberry.schema import Schema
import strawberry
from strawberry.relay import Node, NodeID

# Create a Node type with NodeID
@strawberry.type
class User(Node):
    id: NodeID[str]
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def node(self) -> User:
        return User(id="user-1", name="John Doe")

# Create schema for testing
test_schema = Schema(query=Query)

def test_relay_node_id_codegen():
    # Create query file path
    query_path = Path(__file__).parent / "queries" / "relay_node_id.graphql"
    
    # Create code generator
    plugin = PythonPlugin(query_path)
    generator = QueryCodegen(test_schema, plugins=[plugin])
    
    # Run the codegen
    result = generator.run(query_path.read_text())
    code = result.to_string()
    
    # Check that the generated code uses `id: str` and not `_id: str`
    assert "id: str" in code
    assert "_id: str" not in code

    # Also check the Node type itself
    assert "class GetNodeWithIDNode" in code