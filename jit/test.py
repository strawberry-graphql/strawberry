from functools import lru_cache
from inspect import isawaitable
from typing import Any

import strawberry
from strawberry.extensions import DisableValidation, ParserCache
from strawberry.extensions.base_extension import SchemaExtension

from .compiler import compile as jit_compile

TOTAL_RESULTS = 10_000


@strawberry.type
class User:
    id: strawberry.ID
    name: str

    @strawberry.field
    @staticmethod
    async def articles(root, info) -> list["Article"]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}") for i in range(10)
        )


@strawberry.type
class Article:
    id: strawberry.ID
    title: str


@strawberry.type
class Query:
    @strawberry.field
    @staticmethod
    async def users(root, info) -> list[User]:
        return list(
            User(id=strawberry.ID(str(i)), name=f"User {i}")
            for i in range(TOTAL_RESULTS)
        )

    @strawberry.field
    @staticmethod
    async def articles(root, info) -> list[Article]:
        return list(
            Article(id=strawberry.ID(str(i)), title=f"Article {i}")
            for i in range(TOTAL_RESULTS)
        )


class TestExtension(SchemaExtension):
    async def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = _next(root, info, *args, **kwargs)

        if isawaitable(result):
            result = await result

        return result


class NoResolveExtension(SchemaExtension):
    pass


query = """
{
    users {
        id
        name
        articles { id title }
    }
    articles { id title }
}
"""


async def _original_execution(schema) -> Any:
    result = await schema.execute(query)

    return result.data


@lru_cache
def _full_compile(query, schema) -> Any:
    function_code = jit_compile(query, schema)

    namespace = {
        "Query": Query,
        "User": User,
        "Article": Article,
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


async def _jitted_execution(schema, warmup: bool = False) -> Any:
    code, fun = _full_compile(query, schema)

    if warmup:
        import rich
        from rich.syntax import Syntax

        rich.print("Query:")

        rich.print(Syntax(query, "graphql", theme="dracula"))
        rich.print("Compiled:")
        rich.print(Syntax(code, "python", theme="dracula", line_numbers=True))

    try:
        return await fun(schema, {})
    except Exception as e:
        import pathlib

        pathlib.Path("error.py").write_text(code)

        raise e


extensions_combinations = [
    # [DisableValidation(), ParserCache(), TestExtension()],
    [DisableValidation(), ParserCache()],
]


async def bench():
    import time

    from tabulate import tabulate


    def _get_title(schema):
        return " + ".join(
            extension.__class__.__name__ for extension in schema.extensions
        )

    schemas = [
        strawberry.Schema(query=Query, extensions=extensions)
        for extensions in extensions_combinations
    ]

    # Warmup

    for schema in schemas:
        print(
            "Warming up...",
            _get_title(schema),
        )

        await _original_execution(schema)

        await _jitted_execution(schema, warmup=True)

    print()

    results = []

    for schema in schemas:
        title = _get_title(schema)

        print("Benchmarking...", title)

        start = time.time()
        result = await _original_execution(schema)
        original_time = time.time() - start

        results.append((title, original_time))

        # jitted

        print("Benchmarking...", "JIT" + title)

        start = time.time()
        jit_result = await _jitted_execution(schema)
        jit_time = time.time() - start

        results.append(("JIT " + title, jit_time))

        if result != jit_result:
            import json
            import pathlib

            print("Results don't match")

            pathlib.Path("a.json").write_text(json.dumps(result, indent=2))
            pathlib.Path("b.json").write_text(json.dumps(jit_result, indent=2))
            return

        # # a
        # start = time.time()
        # a_hand_result = await a_compiled_operation(schema, {})
        # a_time = time.time() - start
        #
        # results.append(("A " + title, a_time))
        #
        # if result != a_hand_result:
        #     import json
        #     import pathlib
        #
        #     print("Results don't match")
        #
        #     pathlib.Path("a.json").write_text(json.dumps(result, indent=2))
        #     pathlib.Path("b.json").write_text(json.dumps(a_hand_result, indent=2))
        #     return

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
