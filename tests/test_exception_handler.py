import os

from strawberry.exceptions import MissingFieldAnnotationError, exception_handler


def test_exception_handler(mocker):
    print_mock = mocker.patch("rich.print", autospec=True)

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    exception_handler(MissingFieldAnnotationError, exception, None)

    assert print_mock.call_args == mocker.call(exception)


def test_exception_handler_other_exceptions(mocker):
    print_mock = mocker.patch("rich.print", autospec=True)
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.original_exception_hook", autospec=True
    )

    exception = ValueError("abc")

    exception_handler(ValueError, exception, None)

    assert print_mock.called is False
    assert original_exception_mock.call_args == mocker.call(ValueError, exception, None)


def test_exception_handler_uses_original_when_rich_is_not_installed(mocker):
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.original_exception_hook", autospec=True
    )

    mocker.patch.dict("sys.modules", {"rich": None})

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    exception_handler(MissingFieldAnnotationError, exception, None)

    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )


def test_exception_handler_uses_original_when_disabled_via_env_var(mocker):
    print_mock = mocker.patch("rich.print", autospec=True)
    original_exception_mock = mocker.patch(
        "strawberry.exceptions.original_exception_hook", autospec=True
    )

    mocker.patch.dict(os.environ, {"STRAWBERRY_DISABLE_RICH_ERRORS": "true"})

    class Query:
        abc: int

    exception = MissingFieldAnnotationError("abc", Query)

    exception_handler(MissingFieldAnnotationError, exception, None)

    assert print_mock.called is False
    assert original_exception_mock.call_args == mocker.call(
        MissingFieldAnnotationError, exception, None
    )
