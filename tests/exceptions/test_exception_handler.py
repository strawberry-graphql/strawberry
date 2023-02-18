import os
import sys

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


def test_setup_install_handler(mocker):
    reset_exception_handler()
    setup_exception_handler()

    assert sys.excepthook == strawberry_exception_handler


def test_setup_does_not_install_handler_when_disabled_via_env(mocker):
    reset_exception_handler()

    mocker.patch.dict(os.environ, {"STRAWBERRY_DISABLE_RICH_ERRORS": "true"})

    setup_exception_handler()

    assert sys.excepthook != strawberry_exception_handler
