from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExceptionSource:
    path: Path
    code: str
    start_line: int
    end_line: int
    error_line: int
    error_column: int
    error_column_end: int

    @property
    def path_relative_to_cwd(self) -> Path:
        if self.path.is_absolute():
            return self.path.relative_to(Path.cwd())

        return self.path
