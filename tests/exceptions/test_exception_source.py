import sys
from pathlib import Path

import pytest

from strawberry.exceptions.exception_source import ExceptionSource

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="Test is meant to run on Unix systems"
)


def test_returns_relative_path(mocker):
    mocker.patch.object(Path, "cwd", return_value="/home/user/project/")

    source = ExceptionSource(
        path=Path("/home/user/project/src/main.py"),
        code="",
        start_line=1,
        end_line=1,
        error_line=1,
        error_column=1,
        error_column_end=1,
    )

    assert source.path_relative_to_cwd == Path("src/main.py")


def test_returns_relative_path_when_is_already_relative():
    source = ExceptionSource(
        path=Path("src/main.py"),
        code="",
        start_line=1,
        end_line=1,
        error_line=1,
        error_column=1,
        error_column_end=1,
    )

    assert source.path_relative_to_cwd == Path("src/main.py")
