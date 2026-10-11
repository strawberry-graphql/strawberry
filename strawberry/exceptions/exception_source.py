import os
from dataclasses import dataclass
from pathlib import Path


def path_relative_to_cwd(path: Path) -> Path:
    """Return ``path`` relative to the current working directory when possible.

    Paths outside the current working directory (for example a script run
    with ``python ../app.py``, or a module in site-packages) are returned as
    absolute paths. Paths are normalized first, as script paths can contain
    ``..``, like ``/project/src/../app.py``, and relative paths can come from
    relative ``sys.path`` entries.
    """
    cwd = Path.cwd()
    # `cwd / path` is `path` itself when it's absolute
    absolute = Path(os.path.normpath(cwd / path))

    try:
        return absolute.relative_to(cwd)
    except ValueError:
        return absolute


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
