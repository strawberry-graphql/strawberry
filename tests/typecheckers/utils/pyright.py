from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import TypedDict, cast

from .result import Result, ResultType


class PyrightCLIResult(TypedDict):
    version: str
    time: str
    generalDiagnostics: list[GeneralDiagnostic]
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


def run_pyright(code: str, strict: bool = True) -> list[Result]:
    if strict:
        code = "# pyright: strict\n" + code

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)

    process_result = subprocess.run(
        ["pyright", "--outputjson", f.name], stdout=subprocess.PIPE, check=False
    )

    os.unlink(f.name)  # noqa: PTH108

    pyright_result: PyrightCLIResult = json.loads(process_result.stdout.decode("utf-8"))

    result = [
        Result(
            type=cast(ResultType, diagnostic["severity"].strip()),
            message=diagnostic["message"].strip(),
            line=diagnostic["range"]["start"]["line"],
            column=diagnostic["range"]["start"]["character"] + 1,
        )
        for diagnostic in pyright_result["generalDiagnostics"]
    ]

    # make sure that results are sorted by line and column and then message
    result.sort(key=lambda x: (x.line, x.column, x.message))

    return result
