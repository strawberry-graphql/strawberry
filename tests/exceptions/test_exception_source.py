import sys
from pathlib import Path

import pytest

from strawberry.exceptions import ScalarAlreadyRegisteredError
from strawberry.exceptions.exception_source import ExceptionSource
from strawberry.types.scalar import ScalarDefinition

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


def test_returns_absolute_path_when_outside_cwd(mocker):
    mocker.patch.object(Path, "cwd", return_value=Path("/home/user/project/"))

    source = ExceptionSource(
        path=Path("/home/user/scripts/main.py"),
        code="",
        start_line=1,
        end_line=1,
        error_line=1,
        error_column=1,
        error_column_end=1,
    )

    assert source.path_relative_to_cwd == Path("/home/user/scripts/main.py")


def test_scalar_already_registered_error_with_other_scalar_outside_cwd(mocker):
    mocker.patch.object(Path, "cwd", return_value=Path("/home/user/project/"))

    def make_scalar(source_file: str) -> ScalarDefinition:
        return ScalarDefinition(
            name="MyScalar",
            description=None,
            specified_by_url=None,
            serialize=None,
            parse_value=None,
            parse_literal=None,
            _source_file=source_file,
            _source_line=1,
        )

    error = ScalarAlreadyRegisteredError(
        make_scalar("/home/user/project/main.py"),
        make_scalar("/home/user/lib/scalars.py"),
    )

    assert "/home/user/lib/scalars.py:1" in error.suggestion
