#!/usr/bin/env python
"""Debug the optimized JIT compiler to see generated code."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List

import strawberry
from strawberry.jit_compiler_optimized import OptimizedGraphQLJITCompiler


@strawberry.type
class Author:
    id: int
    name: str


@strawberry.type
class Post:
    id: int
    title: str
    author: Author


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        return [
            Post(id=1, title="Post 1", author=Author(id=1, name="Author 1")),
            Post(id=2, title="Post 2", author=Author(id=2, name="Author 2")),
        ]


schema = strawberry.Schema(Query)

query = """
{
    posts {
        id
        title
        author {
            id
            name
        }
    }
}
"""

compiler = OptimizedGraphQLJITCompiler(schema._schema)

# Get the generated code
from graphql import parse

document = parse(query)
operation = compiler._get_operation(document)
root_type = schema._schema.query_type

generated_code = compiler._generate_optimized_function(operation, root_type)

print("Generated Code:")
print("=" * 60)
print(generated_code)
print("=" * 60)

# Try to compile it
try:
    compiled_code = compile(generated_code, "<test>", "exec")
    print("\n✅ Code compiles successfully!")
except SyntaxError as e:
    print(f"\n❌ Syntax Error: {e}")
    print(f"   Line {e.lineno}: {e.text}")
