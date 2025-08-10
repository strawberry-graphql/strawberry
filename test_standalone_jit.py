#!/usr/bin/env python
"""Test executing the standalone JIT-compiled file."""

import sys

# Import the generated standalone file
sys.path.insert(0, ".inline-snapshot/external")
from b2d1576f957a3e2e48303bf3cf8a6fef340a03e0755417106cb66e6e291aae34 import (
    execute_query,
)


# Create test data matching the expected schema
class Post:
    def __init__(self, id, title):
        self.id = id
        self.title = title


class Query:
    def __init__(self):
        self.posts = [
            Post(id="1", title="First Post"),
            Post(id="2", title="Second Post"),
        ]


# Execute the standalone JIT function
root = Query()
result = execute_query(root)

print("Standalone execution result:")
print(result)

# Verify it works
assert result == {
    "posts": [{"id": "1", "title": "First Post"}, {"id": "2", "title": "Second Post"}]
}
print("\n✅ Standalone JIT execution successful!")
