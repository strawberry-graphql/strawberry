#!/usr/bin/env python
"""Trace indentation levels in the optimized JIT compiler."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List

import strawberry
from strawberry.jit_compiler_optimized import OptimizedGraphQLJITCompiler


class TracingOptimizedCompiler(OptimizedGraphQLJITCompiler):
    def _emit(self, line: str):
        indent = "    " * self.indent_level
        self.generated_code.append(f"{indent}{line}")
        print(f"[Level {self.indent_level}] {indent}{line}")


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
        return []


schema = strawberry.Schema(Query)

query = """
{
    posts {
        id
        title
    }
}
"""

compiler = TracingOptimizedCompiler(schema._schema)

from graphql import parse

document = parse(query)
operation = compiler._get_operation(document)
root_type = schema._schema.query_type

print("Tracing indentation levels:")
print("=" * 60)
generated_code = compiler._generate_optimized_function(operation, root_type)
print("=" * 60)
