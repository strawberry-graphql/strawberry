from dataclasses import dataclass
from typing import Literal

ResultType = Literal[
    "error",
    "information",
    "note",
]


@dataclass
class Result:
    type: ResultType
    message: str
    line: int
    column: int
