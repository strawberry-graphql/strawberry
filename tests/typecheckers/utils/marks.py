import shutil
import sys

import pytest


def pyright_exist() -> bool:
    return shutil.which("pyright") is not None


def mypy_exists() -> bool:
    return shutil.which("mypy") is not None


skip_on_windows = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Do not run pyright on windows due to path issues",
)

requires_pyright = pytest.mark.skipif(
    not pyright_exist(),
    reason="These tests require pyright",
)

requires_mypy = pytest.mark.skipif(
    not mypy_exists(),
    reason="These tests require mypy",
)
