#!/usr/bin/env python
"""Debug resolver map generation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List

from graphql import parse

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler


@strawberry.type
class Post:
    id: str
    title: str


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        return [
            Post(id="1", title="Post 1"),
            Post(id="2", title="Post 2"),
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

# First, generate with compiler to see resolver map
compiler = GraphQLJITCompiler(schema._schema)
document = parse(query)
operation = compiler._get_operation(document)
root_type = schema._schema.type_map["Query"]

print("Before generation:")
print(f"  resolver_map: {compiler.resolver_map}")
print(f"  field_counter: {compiler.field_counter}")

# Generate the function code
generated_code = compiler._generate_function(operation, root_type)

print("\nAfter generation:")
print(f"  resolver_map keys: {list(compiler.resolver_map.keys())}")
print(f"  field_counter: {compiler.field_counter}")

for rid, resolver in compiler.resolver_map.items():
    print(f"  {rid}: {resolver}")

# Now compile it properly
print("\n\nCompiling query properly:")
compiler2 = GraphQLJITCompiler(schema._schema)
compiled_fn = compiler2.compile_query(query)

print(f"\nCompiler2 resolver_map after compile: {list(compiler2.resolver_map.keys())}")

# Execute
root = Query()
result = compiled_fn(root)
print(f"Result: {result}")
