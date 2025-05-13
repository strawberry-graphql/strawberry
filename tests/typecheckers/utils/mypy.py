from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
from typing import TypedDict

from .result import Result


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


def run_mypy(code: str, strict: bool = True) -> list[Result]:
    args = ["mypy", "--output=json"]

    if strict:
        args.append("--strict")

    with tempfile.TemporaryDirectory() as directory:
        module_path = pathlib.Path(directory) / "mypy_test.py"
        module_path.write_text(code)

        process_result = subprocess.run(
            [*args, str(module_path)], check=False, capture_output=True
        )

        full_output = (
            process_result.stdout.decode("utf-8")
            + "\n"
            + process_result.stderr.decode("utf-8")
        )
        full_output = full_output.strip()

        results: list[Result] = []

        try:
            for line in full_output.split("\n"):
                mypy_result = json.loads(line)

                results.append(
                    Result(
                        type=mypy_result["severity"].strip(),
                        message=mypy_result["message"].strip(),
                        line=mypy_result["line"],
                        column=mypy_result["column"] + 1,
                    )
                )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {full_output}") from e

        results.sort(key=lambda x: (x.line, x.column, x.message))

        return results
