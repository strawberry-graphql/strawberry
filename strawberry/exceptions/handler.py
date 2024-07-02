import os
import sys
import threading
from types import TracebackType
from typing import Any, Callable, Optional, Tuple, Type, cast

from .exception import StrawberryException, UnableToFindExceptionSource

original_threading_exception_hook = threading.excepthook


ExceptionHandler = Callable[
    [Type[BaseException], BaseException, Optional[TracebackType]], None
]


def should_use_rich_exceptions() -> bool:
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
            ) -> None:
                try:
                    rich.print(exception)

                # we check if weren't able to find the exception source
                # in that case we fallback to the original exception handler
                except UnableToFindExceptionSource:
                    sys.__excepthook__(exception_type, exception, traceback)

            return _handler

    return sys.__excepthook__


def strawberry_exception_handler(
    exception_type: Type[BaseException],
    exception: BaseException,
    traceback: Optional[TracebackType],
) -> None:
    _get_handler(exception_type)(exception_type, exception, traceback)


def strawberry_threading_exception_handler(
    args: Tuple[
        Type[BaseException],
        Optional[BaseException],
        Optional[TracebackType],
        Optional[threading.Thread],
    ],
) -> None:
    (exception_type, exception, traceback, _) = args

    if exception is None:
        # this cast is only here because some weird issue with mypy
        # and the inability to disable this error based on the python version
        # (we'd need to do type ignore for python 3.8 and above, but mypy
        # doesn't seem to be able to handle that and will complain in python 3.7)

        cast(Any, original_threading_exception_hook)(args)

        return

    _get_handler(exception_type)(exception_type, exception, traceback)


def reset_exception_handler() -> None:
    sys.excepthook = sys.__excepthook__

    threading.excepthook = original_threading_exception_hook


def setup_exception_handler() -> None:
    if should_use_rich_exceptions():
        sys.excepthook = strawberry_exception_handler

        threading.excepthook = strawberry_threading_exception_handler
