from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import List, TypedDict, cast
from typing_extensions import Literal

import pytest

ResultType = Literal["error", "information"]


class PyrightCLIResult(TypedDict):
    version: str
    time: str
    generalDiagnostics: List[GeneralDiagnostic]
    summary: Summary


class GeneralDiagnostic(TypedDict):
    file: str
    severity: str
    message: str
    range: Range


class Range(TypedDict):
    start: EndOrStart
    end: EndOrStart


class EndOrStart(TypedDict):
    line: int
    character: int


class Summary(TypedDict):
    filesAnalyzed: int
    errorCount: int
    warningCount: int
    informationCount: int
    timeInSec: float


@dataclass
class Result:
    type: ResultType
    message: str
    line: int
    column: int


def run_pyright(code: str, strict: bool = True) -> List[Result]:
    if strict:
        code = "# pyright: strict\n" + code

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)

    process_result = subprocess.run(
        ["pyright", "--outputjson", f.name], stdout=subprocess.PIPE, check=False
    )

    os.unlink(f.name)  # noqa: PTH108

    pyright_result: PyrightCLIResult = json.loads(process_result.stdout.decode("utf-8"))

    return [
        Result(
            type=cast(ResultType, diagnostic["severity"]),
            message=diagnostic["message"],
            line=diagnostic["range"]["start"]["line"],
            column=diagnostic["range"]["start"]["character"] + 1,
        )
        for diagnostic in pyright_result["generalDiagnostics"]
    ]


def pyright_exist() -> bool:
    return shutil.which("pyright") is not None


skip_on_windows = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Do not run pyright on windows due to path issues",
)

requires_pyright = pytest.mark.skipif(
    not pyright_exist(),
    reason="These tests require pyright",
)
