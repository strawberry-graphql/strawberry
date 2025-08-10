#!/usr/bin/env python
"""Debug the standalone JIT compilation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List

from graphql import parse

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler


@strawberry.type
class Author:
    id: str
    name: str


@strawberry.type
class Post:
    id: str
    title: str
    author: Author


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        return [
            Post(id="1", title="Post 1", author=Author(id="a1", name="Alice")),
            Post(id="2", title="Post 2", author=Author(id="a2", name="Bob")),
        ]


schema = strawberry.Schema(Query)

query = """
query {
    posts {
        id
        title
    }
}
"""

compiler = GraphQLJITCompiler(schema._schema)
document = parse(query)
operation = compiler._get_operation(document)
root_type = schema._schema.type_map["Query"]

# Generate the function code
generated_code = compiler._generate_function(operation, root_type)

print("Generated Code:")
print("=" * 60)
print(generated_code)
print("=" * 60)

# Try to execute it
print("\nCompiling and executing...")
compiled_fn = compiler.compile_query(query)
root = Query()
result = compiled_fn(root)
print(f"Result: {result}")

# Check resolver map
print(f"\nResolver map: {compiler.resolver_map}")
for rid, resolver in compiler.resolver_map.items():
    print(f"  {rid}: {resolver}")
