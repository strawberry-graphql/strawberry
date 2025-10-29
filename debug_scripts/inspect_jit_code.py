"""Inspect generated JIT code to debug performance issue."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from schema import schema  # type: ignore
from strawberry.jit import compile_query

# Simple query for testing
QUERY = """
query TestQuery {
    posts(limit: 10) {
        id
        title
        content
        wordCount
        author {
            name
            email
            bio
            postsCount
        }
        comments(limit: 5) {
            id
            text
            likes
            author {
                name
            }
        }
    }
    featuredPost {
        id
        title
        viewCount
    }
}
"""

# Compile query
compiled_fn = compile_query(schema, QUERY)

# Print generated code
print("=" * 80)
print("GENERATED JIT CODE:")
print("=" * 80)
print(compiled_fn._jit_source)
print("=" * 80)
