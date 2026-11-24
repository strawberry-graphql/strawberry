import os
import subprocess
import sys
import textwrap
import types

import pytest

from strawberry.exceptions import MissingFieldAnnotationError
from strawberry.exceptions.handler import (
    reset_exception_handler,
    setup_exception_handler,
    strawberry_exception_handler,
)


def test_exception_handler(mocker):
    print_mock = mocker.patch("rich.print", autospec=True)

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    strawberry_exception_handler(MissingFieldAnnotationError, exception, None)

    assert print_mock.call_args == mocker.call(exception)


def test_exception_handler_other_exceptions(mocker):
    print_mock = mocker.patch("rich.print", autospec=True)
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.handler.sys.__excepthook__", autospec=True
    )

    exception = ValueError("abc")

    strawberry_exception_handler(ValueError, exception, None)

    assert print_mock.called is False
    assert original_exception_mock.call_args == mocker.call(ValueError, exception, None)


def test_exception_handler_uses_original_when_rich_is_not_installed(mocker):
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.handler.sys.__excepthook__", autospec=True
    )

    mocker.patch.dict("sys.modules", {"rich": None})

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    strawberry_exception_handler(MissingFieldAnnotationError, exception, None)

    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )


def test_exception_handler_uses_original_when_libcst_is_not_installed(mocker):
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.handler.sys.__excepthook__", autospec=True
    )

    mocker.patch.dict("sys.modules", {"libcst": None})

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    strawberry_exception_handler(MissingFieldAnnotationError, exception, None)

    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )


def test_exception_handler_uses_original_when_source_cannot_be_found(
    mocker, monkeypatch
):
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.handler.sys.__excepthook__", autospec=True
    )

    # a module without `__file__` or any other location, like `__main__`
    # when using `python -c` or the REPL
    module = types.ModuleType("strawberry_test_module_without_file")
    monkeypatch.setitem(sys.modules, module.__name__, module)

    class Query:
        abc: int

    Query.__module__ = module.__name__

    exception = MissingFieldAnnotationError("abc", Query)

    strawberry_exception_handler(MissingFieldAnnotationError, exception, None)

    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )


def test_exception_handler_uses_original_when_rendering_fails(mocker):
    mocker.patch("rich.print", autospec=True, side_effect=RuntimeError("oops"))
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.handler.sys.__excepthook__", autospec=True
    )

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    strawberry_exception_handler(MissingFieldAnnotationError, exception, None)

    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )


def test_exception_handler_shows_error_raised_from_script(tmp_path):
    pytest.importorskip("libcst")
    pytest.importorskip("rich")

    script = tmp_path / "app.py"
    script.write_text(
        textwrap.dedent(
            """
            import strawberry


            @strawberry.type
            class Query:
                @strawberry.field
                def hello(self):
                    return "hi"
            """
        ),
        encoding="utf-8",
    )
    # run from another directory, so the script isn't relative to the cwd
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    env = {
        key: value
        for key, value in os.environ.items()
        if key != "STRAWBERRY_DISABLE_RICH_ERRORS"
    }
    env["COLUMNS"] = "200"

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env=env,
        # fails the test instead of hanging the test run
        timeout=60,
    )

    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "Error in sys.excepthook" not in output
    assert "Traceback" not in output
    assert "error: Missing annotation for field `hello`" in output
    assert "resolver missing annotation" in output


def test_setup_install_handler(mocker):
    reset_exception_handler()
    setup_exception_handler()

    assert sys.excepthook == strawberry_exception_handler


def test_setup_does_not_install_handler_when_disabled_via_env(mocker):
    reset_exception_handler()

    mocker.patch.dict(os.environ, {"STRAWBERRY_DISABLE_RICH_ERRORS": "true"})

    setup_exception_handler()

    assert sys.excepthook != strawberry_exception_handler
