from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass

from .mypy import run_mypy
from .pyright import run_pyright
from .result import Result


@dataclass
class TypecheckResult:
    pyright: list[Result]
    mypy: list[Result]


def typecheck(code: str, strict: bool = True) -> TypecheckResult:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        pyright_future = executor.submit(run_pyright, code, strict=strict)
        mypy_future = executor.submit(run_mypy, code, strict=strict)

        pyright_results = pyright_future.result()
        mypy_results = mypy_future.result()

    return TypecheckResult(pyright=pyright_results, mypy=mypy_results)
