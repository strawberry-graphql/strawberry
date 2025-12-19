from __future__ import annotations

import os
import pathlib
import re
import subprocess
import tempfile
from typing import cast

from .result import Result, ResultType


def run_ty(code: str, strict: bool = True) -> list[Result]:
    # ty uses concise output format which includes revealed type info
    # Format: <file>:<line>:<col>: <severity>[<check_name>] <message>
    args = [
        "ty",
        "check",
        "--output-format",
        "concise",
        # Ignore the warning about using reveal_type without importing it
        "--ignore",
        "undefined-reveal",
        "--color",
        "never",
    ]

    with tempfile.TemporaryDirectory() as directory:
        module_path = pathlib.Path(directory) / "ty_test.py"
        module_path.write_text(code)

        process_result = subprocess.run(
            [*args, str(module_path)],
            check=False,
            capture_output=True,
            env={
                "PATH": os.environ["PATH"],
            },
        )

        full_output = (
            process_result.stdout.decode("utf-8")
            + "\n"
            + process_result.stderr.decode("utf-8")
        )
        full_output = full_output.strip()

        results: list[Result] = []

        # Parse the concise output format
        # Format: <file>:<line>:<col>: <severity>[<check_name>] <message>
        pattern = re.compile(r"^.*?:(\d+):(\d+): (error|warning|info)\[[\w-]+\] (.+)$")

        for raw_line in full_output.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if match:
                line_num = int(match.group(1))
                col_num = int(match.group(2))
                severity = match.group(3)
                message = match.group(4)

                # Map ty severities to our ResultType
                # ty uses: error, warning, info
                # Our ResultType uses: error, information, note
                type_mapping = {
                    "error": "error",
                    "warning": "error",  # treat warnings as errors for consistency
                    "info": "information",
                }
                result_type = type_mapping.get(severity, "note")

                results.append(
                    Result(
                        type=cast("ResultType", result_type),
                        message=message.strip(),
                        line=line_num,
                        column=col_num,
                    )
                )

        # Sort results by line, column, and message for consistent ordering
        results.sort(key=lambda x: (x.line, x.column, x.message))

        return results
