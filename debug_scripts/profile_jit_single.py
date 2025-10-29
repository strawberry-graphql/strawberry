"""Profile single JIT execution."""

import asyncio
import cProfile
import pstats
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from schema import Query, schema  # type: ignore
from strawberry.jit import compile_query

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


async def main():
    root = Query()
    compiled_fn = compile_query(schema, QUERY)

    print("Profiling JIT execution...")
    profiler = cProfile.Profile()
    profiler.enable()

    await compiled_fn(root)

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    print(s.getvalue())


if __name__ == "__main__":
    asyncio.run(main())
