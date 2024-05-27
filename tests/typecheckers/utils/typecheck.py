from __future__ import annotations

from dataclasses import dataclass

from .mypy import run_mypy
from .pyright import run_pyright
from .result import Result


@dataclass
class TypecheckResult:
    pyright: list[Result]
    mypy: list[Result]


def typecheck(code: str, strict: bool = True) -> TypecheckResult:
    pyright_results = run_pyright(code, strict=strict)
    mypy_results = run_mypy(code, strict=strict)

    return TypecheckResult(pyright=pyright_results, mypy=mypy_results)
