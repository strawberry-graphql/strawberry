import os
import sys
import threading
from types import TracebackType
from typing import Callable, Optional, Tuple, Type

from .exception import StrawberryException, UnableToFindExceptionSource


original_exception_hook = sys.excepthook


if sys.version_info >= (3, 8):
    original_threading_exception_hook = threading.excepthook
else:
    original_threading_exception_hook = None

ExceptionHandler = Callable[
    [Type[BaseException], BaseException, Optional[TracebackType]], None
]


def should_use_rich_exceptions():
    errors_disabled = os.environ.get("STRAWBERRY_DISABLE_RICH_ERRORS", "")

    return errors_disabled.lower() not in ["true", "1", "yes"]


def _get_handler(exception_type: Type[BaseException]) -> ExceptionHandler:
    if issubclass(exception_type, StrawberryException):
        try:
            import rich
        except ImportError:
            pass
        else:

            def _handler(
                exception_type: Type[BaseException],
                exception: BaseException,
                traceback: Optional[TracebackType],
            ):
                try:
                    rich.print(exception)

                # we check if weren't able to find the exception source
                # in that case we fallback to the original exception handler
                except UnableToFindExceptionSource:
                    original_exception_hook(exception_type, exception, traceback)

            return _handler

    return original_exception_hook


def strawberry_exception_handler(
    exception_type: Type[BaseException],
    exception: BaseException,
    traceback: Optional[TracebackType],
):
    _get_handler(exception_type)(exception_type, exception, traceback)


def strawberry_threading_exception_handler(
    args: Tuple[
        Type[BaseException],
        Optional[BaseException],
        Optional[TracebackType],
        Optional[threading.Thread],
    ]
):
    (exception_type, exception, traceback, _) = args

    if exception is None:
        assert original_threading_exception_hook  # type: ignore[truthy-function]

        original_threading_exception_hook(args)  # type: ignore[arg-type]

        return

    _get_handler(exception_type)(exception_type, exception, traceback)


def reset_exception_handler():
    sys.excepthook = original_exception_hook

    if original_threading_exception_hook:  # type: ignore[truthy-function]
        threading.excepthook = original_threading_exception_hook


def setup_exception_handler():
    if should_use_rich_exceptions():
        sys.excepthook = strawberry_exception_handler

        if original_threading_exception_hook:  # type: ignore[truthy-function]
            threading.excepthook = strawberry_threading_exception_handler
