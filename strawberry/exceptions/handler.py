import os
import sys
from types import TracebackType
from typing import Callable, Optional, Type

from .exception import StrawberryException


original_exception_hook = sys.excepthook

ExceptionHandler = Callable[
    [Type[BaseException], BaseException, Optional[TracebackType]], None
]


def _should_use_rich_exceptions():
    errors_disabled = os.environ.get("STRAWBERRY_DISABLE_RICH_ERRORS", "")

    return errors_disabled.lower() not in ["true", "1", "yes"]


def strawberry_exception_handler(
    exception_type: Type[BaseException],
    exception: BaseException,
    traceback: Optional[TracebackType],
):
    def _get_handler() -> ExceptionHandler:
        if (
            issubclass(exception_type, StrawberryException)
            and _should_use_rich_exceptions()
        ):
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
                    rich.print(exception)

                return _handler

        return original_exception_hook

    _get_handler()(exception_type, exception, traceback)


def setup_exception_handler():
    sys.excepthook = strawberry_exception_handler
