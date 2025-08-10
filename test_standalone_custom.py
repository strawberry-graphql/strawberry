#!/usr/bin/env python
"""Test executing the standalone JIT-compiled file with custom resolvers."""

import sys

# Import the generated standalone file for custom resolver test
sys.path.insert(0, ".inline-snapshot/external")
import importlib.util

spec = importlib.util.spec_from_file_location(
    "custom_jit",
    ".inline-snapshot/external/98f2e3eb8e99916861b5bf85065360a0b759ac2daf47ce59ecbfbf717e0fc427.py",
)
custom_jit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custom_jit)
execute_query = custom_jit.execute_query


# Create test data matching the expected schema
class AuthorWithCustomField:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        self.displayName = f"{name} <{email}>"  # Simulating custom field


class PostWithSummary:
    def __init__(self, id, title, content, author):
        self.id = id
        self.title = title
        self.content = content
        self.author = author
        self.summary = f"{title}: {content[:20]}..."  # Simulating custom resolver


class QueryWithCustom:
    def __init__(self):
        self.posts = [
            PostWithSummary(
                id="1",
                title="First Post",
                content="Hello World",
                author=AuthorWithCustomField(
                    id="a1", name="Alice", email="alice@example.com"
                ),
            ),
            PostWithSummary(
                id="2",
                title="Second Post",
                content="GraphQL is great",
                author=AuthorWithCustomField(
                    id="a2", name="Bob", email="bob@example.com"
                ),
            ),
        ]


# Execute the standalone JIT function
root = QueryWithCustom()
result = execute_query(root)

print("Standalone execution result with custom resolvers:")
print(result)

# Verify it works
expected = {
    "posts": [
        {
            "title": "First Post",
            "summary": "First Post: Hello World...",
            "author": {"displayName": "Alice <alice@example.com>"},
        },
        {
            "title": "Second Post",
            "summary": "Second Post: GraphQL is great...",
            "author": {"displayName": "Bob <bob@example.com>"},
        },
    ]
}

assert result == expected
print("\n✅ Standalone JIT execution with custom resolvers successful!")
