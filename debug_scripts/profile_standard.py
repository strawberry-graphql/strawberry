"""Profile standard GraphQL execution."""

import asyncio
import cProfile
import pstats
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from graphql import execute, parse

from schema import Query, schema  # type: ignore

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
    parsed_query = parse(QUERY)

    print("Profiling standard GraphQL execution...")
    profiler = cProfile.Profile()
    profiler.enable()

    await execute(schema._schema, parsed_query, root_value=root)

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    print(s.getvalue())


if __name__ == "__main__":
    asyncio.run(main())
