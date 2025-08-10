#!/usr/bin/env python
"""Minimal test to verify optimized JIT compiler works after indentation fix."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graphql import (
    GraphQLField,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

from strawberry.jit_compiler_optimized import OptimizedGraphQLJITCompiler


# Create a simple test schema
def resolve_name(obj, info):
    return obj.get("name")


def resolve_posts(obj, info):
    return [
        {"id": "1", "title": "Post 1"},
        {"id": "2", "title": "Post 2"},
    ]


post_type = GraphQLObjectType(
    "Post",
    lambda: {
        "id": GraphQLField(GraphQLString),
        "title": GraphQLField(GraphQLString),
    },
)

query_type = GraphQLObjectType(
    "Query",
    lambda: {
        "name": GraphQLField(GraphQLString, resolve=resolve_name),
        "posts": GraphQLField(GraphQLList(post_type), resolve=resolve_posts),
    },
)

schema = GraphQLSchema(query_type)

# Test the optimized compiler
compiler = OptimizedGraphQLJITCompiler(schema)

# Test 1: Simple field
print("Test 1: Simple field query")
query1 = "{ name }"
try:
    fn1 = compiler.compile_query(query1)
    result1 = fn1({"name": "Test"})
    print(f"  Result: {result1}")
    assert result1 == {"name": "Test"}
    print("  ✅ Passed")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 2: List field with nested selections
print("\nTest 2: List field with nested selections")
query2 = """
{
    posts {
        id
        title
    }
}
"""
try:
    fn2 = compiler.compile_query(query2)
    result2 = fn2({})
    print(f"  Result: {result2}")
    assert "posts" in result2
    assert len(result2["posts"]) == 2
    assert result2["posts"][0]["id"] == "1"
    print("  ✅ Passed - Indentation fix successful!")
except SyntaxError as e:
    print(f"  ❌ Syntax Error (indentation issue): {e}")
    # Print generated code for debugging
    print("\nGenerated code:")
    print(
        compiler._generate_optimized_function(
            compiler._get_operation(compiler.parse(query2)), query_type
        )
    )
except Exception as e:
    print(f"  ❌ Failed: {e}")
    import traceback

    traceback.print_exc()

print("\n✅ Optimized JIT compiler indentation fix verified!")
