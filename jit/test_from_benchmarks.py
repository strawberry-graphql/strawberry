from functools import lru_cache
from typing import Any

import strawberry
from strawberry.extensions import DisableValidation, ParserCache

from .compiler import compile as jit_compile


@strawberry.type
class Article:
    id: strawberry.ID
    title: str


@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    async def search(query: str, first: int = 10) -> list[Article]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}") for i in range(10)
        )


schema = strawberry.Schema(query=Query, extensions=[DisableValidation(), ParserCache()])

query = """
query Search ($query: String!) {
    search(query: $query, first: 10) {
       title
   }
}
"""


async def _original_execution(schema, variables=None) -> Any:
    result = await schema.execute(query, variable_values=variables)

    return result.data


@lru_cache
def _full_compile(query, schema) -> Any:
    function_code = jit_compile(query, schema)

    namespace = {
        **globals(),
    }
    try:
        exec(compile(function_code, "<string>", "exec"), namespace)
    except Exception as e:
        print(function_code)
        raise e

    fun = namespace["_compiled_operation"]

    import pathlib

    pathlib.Path("jit/hand/_source.py").write_text(function_code)

    return function_code, fun


async def _jitted_execution(schema, variables, warmup: bool = False) -> Any:
    code, fun = _full_compile(query, schema)

    if warmup:
        import rich
        from rich.syntax import Syntax

        rich.print("Query:")

        rich.print(Syntax(query, "graphql", theme="dracula"))
        rich.print("Compiled:")
        rich.print(Syntax(code, "python", theme="dracula", line_numbers=True))

    try:
        return await fun(schema, {}, variables)
    except Exception as e:
        import pathlib

        pathlib.Path("error.py").write_text(code)

        raise e


async def bench():
    import time

    from tabulate import tabulate

    def _get_title(schema):
        return " + ".join(
            extension.__class__.__name__ for extension in schema.extensions
        )

    print(
        "Warming up...",
        _get_title(schema),
    )

    variables = {"query": "Article"}

    await _original_execution(schema, variables)

    await _jitted_execution(schema, variables, warmup=True)

    print()

    results = []

    title = _get_title(schema)

    print("Benchmarking...", title)

    start = time.time()
    result = await _original_execution(schema, variables)
    original_time = time.time() - start

    results.append((title, original_time))

    # jitted

    print("Benchmarking...", "JIT" + title)

    start = time.time()
    jit_result = await _jitted_execution(schema, variables)
    jit_time = time.time() - start

    results.append(("JIT " + title, jit_time))

    if result != jit_result:
        import json
        import pathlib

        print("Results don't match")

        pathlib.Path("a.json").write_text(json.dumps(result, indent=2))
        pathlib.Path("b.json").write_text(json.dumps(jit_result, indent=2))
        return

    table_data = []

    baseline_time = results[0][1]

    for title, duration in results:
        table_data.append(
            (
                title,
                f"{duration:.4f}s",
                f"{baseline_time/duration:.2f}x",
            )
        )

    # Print formatted table
    print()
    print("Performance Comparison:")
    print(
        tabulate(
            table_data,
            headers=["Version", "Time", "Speed Ratio"],
            tablefmt="fancy_grid",
        )
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(bench())
