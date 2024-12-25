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

    assert not result.errors

    return result.data


@lru_cache
def _full_compile(operation, schema) -> Any:
    function_code = jit_compile(operation, schema)

    namespace = {
        **globals(),
    }
    try:
        exec(compile(function_code, "<string>", "exec"), namespace)

        fun = namespace["_compiled_operation"]
    except Exception as e:
        fun = None
        rich.print("[red]Error during JIT compilation", e)

    return function_code, fun


async def _jitted_execution(operation, variables, name: str | None = None) -> Any:
    code, fun = _full_compile(operation, schema)

    result = None

    if fun:
        try:
            result = await fun(schema, {}, variables)
        except Exception as e:
            rich.print("[red]Error during JIT execution", e)

    return result, code


async def bench(query: pathlib.Path, variables: Any) -> dict | None:
    rich.print()
    operation_text = query.read_text()

    with Live(transient=True) as live:
        live.console.print(f"Benchmarking... [green italic]{query.name}")
        live.console.print("====================================")
        live.console.print("Warming up...")

        try:
            await _original_execution(operation=operation_text, variables=variables)
            await _jitted_execution(
                operation=operation_text, variables=variables, name=query.name
            )
        except Exception as e:
            rich.print("[red]Error during warmup")

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
        jit_result, jitted_code = await _jitted_execution(
            operation=operation_text, variables=variables
        )

        jit_time = time.time() - start

        results.append(("JIT", jit_time))

    if result != jit_result:
        rich.print("[red]Results don't match")

        pathlib.Path("original.json").write_text(json.dumps(result, indent=2))
        pathlib.Path("jit.json").write_text(json.dumps(jit_result, indent=2))

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

    return {
        "id": query.stem,
        "title": query.name,
        "results": [
            {
                "version": "standard",
                "time": f"{original_time:.4f}s",
                "speedRatio": f"{baseline_time/original_time:.2f}x",
            },
            {
                "version": "JIT",
                "time": f"{jit_time:.4f}s",
                "speedRatio": f"{baseline_time/jit_time:.2f}x",
            },
        ],
        "code": jitted_code,
        "query": operation_text,
    }


if __name__ == "__main__":
    import asyncio

    operations = pathlib.Path(__file__).parent / "operations"

    json_output = pathlib.Path(__file__).parent / "web/src/data/benchmarks.json"

    benchmarks = [
        (pathlib.Path(operations / "search.graphql"), {"query": "test", "first": 1000}),
        (
            pathlib.Path(operations / "search_nested.graphql"),
            {"query": "test", "first": 1000},
        ),
    ]

    results = []

    for query, variables in benchmarks:
        result = asyncio.run(bench(query, variables))

        results.append(result)

    json_output.write_text(json.dumps(results, indent=2))
