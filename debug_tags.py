#!/usr/bin/env python
"""Debug the tags field issue in optimized JIT."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List

import strawberry
from strawberry.jit_compiler_optimized import OptimizedGraphQLJITCompiler


@strawberry.type
class Tag:
    id: int
    name: str
    category: str


@strawberry.type
class Content:
    id: int
    title: str
    tags: List[Tag]


@strawberry.type
class Query:
    @strawberry.field
    def contents(self) -> List[Content]:
        return [
            Content(
                id=1, title="Content 1", tags=[Tag(id=1, name="tag1", category="tech")]
            )
        ]


schema = strawberry.Schema(Query)

query = """
{
    contents {
        id
        title
        tags {
            id
            name
            category
        }
    }
}
"""

compiler = OptimizedGraphQLJITCompiler(schema._schema)

from graphql import parse

document = parse(query)
operation = compiler._get_operation(document)
root_type = schema._schema.query_type

generated_code = compiler._generate_optimized_function(operation, root_type)

print("Generated Code:")
print("=" * 60)
print(generated_code)
print("=" * 60)

# Try to run it
try:
    fn = compiler.compile_query(query)
    result = fn(Query())
    print("\nResult:", result)
except Exception as e:
    print(f"\nError: {e}")
    import traceback

    traceback.print_exc()
