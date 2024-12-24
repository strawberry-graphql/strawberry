import json
import pathlib
import time
from functools import lru_cache
from typing import Any

import rich
from rich.table import Table
from rich.live import Live

from .compiler import compile as jit_compile
from .schema import *  # noqa


async def _original_execution(operation, variables=None) -> Any:
    result = await schema.execute(operation, variable_values=variables)

    return result.data


@lru_cache
def _full_compile(operation, schema) -> Any:
    function_code = jit_compile(operation, schema)

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


async def _jitted_execution(operation, variables) -> Any:
    code, fun = _full_compile(operation, schema)

    return await fun(schema, {}, variables)


async def bench(query: pathlib.Path, variables: Any) -> None:
    rich.print()
    operation_text = query.read_text()

    with Live(transient=True) as live:
        live.console.print(f"Benchmarking... [green italic]{query.name}")
        live.console.print("====================================")
        live.console.print("Warming up...")

        await _original_execution(operation=operation_text, variables=variables)
        await _jitted_execution(operation=operation_text, variables=variables)

        live.console.print("=====================================")
        live.console.print("Benchmarking... [blue]standard execution")

        results = []

        start = time.time()
        result = await _original_execution(
            operation=operation_text, variables=variables
        )
        original_time = time.time() - start

        results.append(("standard", original_time))

        live.console.print("Benchmarking... [blue]JIT")

        start = time.time()
        jit_result = await _jitted_execution(
            operation=operation_text, variables=variables
        )
        jit_time = time.time() - start

        results.append(("JIT", jit_time))

    if result != jit_result:
        rich.print("[red]Results don't match")

        pathlib.Path("original.json").write_text(json.dumps(result, indent=2))
        pathlib.Path("jit.json").write_text(json.dumps(jit_result, indent=2))

        raise Exception("Results don't match")

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

    table = Table(title=query.name)
    table.add_column("Version")
    table.add_column("Time")
    table.add_column("Speed Ratio")

    for row in table_data:
        table.add_row(*row)

    rich.print()
    rich.print(table)
    rich.print("=====================================")


if __name__ == "__main__":
    import asyncio

    here = pathlib.Path(__file__).parent

    benchmarks = [
        (
            pathlib.Path(here / "operations/search.graphql"),
            {"query": "test", "first": 1000},
        ),
    ]

    for query, variables in benchmarks:
        asyncio.run(bench(query, variables))
