from dataclasses import dataclass
from pathlib import Path


def path_relative_to_cwd(path: Path) -> Path:
    """Return ``path`` relative to the current working directory when possible.

    Paths outside the current working directory (for example a script run
    with ``python ../app.py``, or a module in site-packages) are returned
    unchanged.
    """
    if not path.is_absolute():
        return path

    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


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
        return path_relative_to_cwd(self.path)
