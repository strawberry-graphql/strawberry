import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import List, cast

import pytest

from typing_extensions import Literal


ResultType = Literal["error", "information"]


@dataclass
class Result:
    type: ResultType
    message: str
    line: int
    column: int

    @classmethod
    def from_output_line(cls, output_line: str) -> "Result":
        # an output line looks like: filename.py:11:6 - type: Message

        file_info, result = output_line.split("-", maxsplit=1)

        line, column = [int(value) for value in file_info.split(":")[1:]]
        type_, message = [value.strip() for value in result.split(":", maxsplit=1)]
        type_ = cast(ResultType, type_)

        return cls(type=type_, message=message, line=line, column=column)


def run_pyright(code: str, strict: bool = True) -> List[Result]:
    if strict:
        code = "# pyright: strict\n" + code

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)

    process_result = subprocess.run(["pyright", f.name], stdout=subprocess.PIPE)

    os.remove(f.name)

    output = process_result.stdout.decode("utf-8")

    results: List[Result] = []

    for line in output.splitlines():
        if line.strip().startswith(f"{f.name}:"):
            result = Result.from_output_line(line)
            if strict:
                result.line -= 1

            results.append(result)

    return results


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
