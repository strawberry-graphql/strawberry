import rich
import json
import pathlib
import time
from functools import lru_cache
from typing import Any

from tabulate import tabulate

from .compiler import compile as jit_compile
from .schema import *  # noqa

query = """
"""


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
    operation_text = query.read_text()

    rich.print("Benchmarking...", query.name)
    rich.print("=====================================")
    rich.print("Warming up...")

    await _original_execution(operation=operation_text, variables=variables)
    await _jitted_execution(operation=operation_text, variables=variables)

    rich.print("=====================================")
    rich.print("Benchmarking... [blue]standard execution")

    results = []

    start = time.time()
    result = await _original_execution(operation=operation_text, variables=variables)
    original_time = time.time() - start

    results.append(("standard", original_time))

    rich.print("Benchmarking... [blue]JIT")

    start = time.time()
    jit_result = await _jitted_execution(operation=operation_text, variables=variables)
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

    # Print formatted table
    rich.print()
    rich.print(
        tabulate(
            table_data,
            headers=["Version", "Time", "Speed Ratio"],
            tablefmt="fancy_grid",
        )
    )


if __name__ == "__main__":
    import asyncio

    here = pathlib.Path(__file__).parent

    benchmarks = [
        (pathlib.Path(here / "operations/search.graphql"), {"query": "test"}),
    ]

    for query, variables in benchmarks:
        asyncio.run(bench(query, variables))
