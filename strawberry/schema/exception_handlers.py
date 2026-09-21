from __future__ import annotations

import types
import typing
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    Union,
    get_args,
    get_origin,
    runtime_checkable,
)
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from strawberry.types.field import StrawberryField
    from strawberry.types.info import Info


ExceptionType = TypeVar("ExceptionType", bound=Exception, contravariant=True)
ErrorType = TypeVar("ErrorType", covariant=True, default=Any)


@runtime_checkable
class ExceptionHandler(Protocol[ExceptionType, ErrorType]):
    """Converts expected Python exceptions into GraphQL union results.

    The exception type the handler receives and the GraphQL error type it
    returns are declared as type parameters::

        class MyHandler(strawberry.ExceptionHandler[MyError, MyErrorType]):
            def handle(self, exception: MyError, *, field, info) -> MyErrorType: ...

    To handle several exception types with one handler, parameterize with
    their union (e.g. ``strawberry.ExceptionHandler[ErrorA | ErrorB,
    MyErrorType]``).

    When a type is only known at runtime, set the ``exception_type`` (a single
    exception type or a collection of them) and/or ``error_type`` class
    attributes instead of parameterizing that slot. Declaring both a type
    parameter and a conflicting attribute for the same slot raises a
    ``TypeError`` at schema creation.

    ``handle`` may decline an individual exception by returning ``None`` (or an
    awaitable resolving to ``None``). Declining re-raises the original exception
    so it propagates as a normal GraphQL error, exactly as if no handler had
    matched. This lets ``handle`` act as a per-instance filter: match a broad
    exception type, but only convert the instances you recognize.
    """

    def handle(
        self,
        exception: ExceptionType,
        *,
        field: StrawberryField,
        info: Info,
    ) -> ErrorType | Awaitable[ErrorType] | None: ...


def _get_declared_types(handler_cls: type) -> tuple[Any, Any]:
    """Type arguments of the ``ExceptionHandler[...]`` base, if any."""
    for klass in handler_cls.__mro__:
        for base in klass.__dict__.get("__orig_bases__", ()):
            if get_origin(base) is not ExceptionHandler:
                continue

            args = get_args(base)
            exception_type = args[0] if args else None
            error_type = args[1] if len(args) > 1 else None

            # An unparameterized (or partially parameterized) generic leaves
            # type variables or the ``Any`` default behind — treat those as
            # not declared.
            if isinstance(exception_type, typing.TypeVar):
                exception_type = None
            if isinstance(error_type, typing.TypeVar) or error_type is Any:
                error_type = None

            return exception_type, error_type

    return None, None


def _normalize_exception_types(value: Any) -> tuple[type[Exception], ...]:
    if isinstance(value, type):
        return (value,)

    if get_origin(value) in (Union, types.UnionType):
        return get_args(value)

    # A collection of types. ``str``/``bytes`` are iterable but never a valid
    # declaration, so keep them whole and let the caller reject them with a
    # clear error rather than silently iterating them into characters.
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return tuple(value)

    return (value,)


def get_exception_types(
    handler: ExceptionHandler[Any],
) -> tuple[type[Exception], ...]:
    attribute = getattr(handler, "exception_type", None)
    declared, _ = _get_declared_types(type(handler))

    if (
        attribute is not None
        and declared is not None
        and set(_normalize_exception_types(attribute))
        != set(_normalize_exception_types(declared))
    ):
        raise TypeError(
            f"Exception handler {type(handler).__name__!r} declares conflicting "
            "exception types via its type parameter and its `exception_type` "
            "attribute. Declare the exception type in one place."
        )

    exception_type = attribute if attribute is not None else declared

    if exception_type is None:
        raise TypeError(
            f"Exception handler {type(handler).__name__!r} does not declare "
            "which exceptions it handles. Parameterize the handler, e.g. "
            "`class MyHandler(strawberry.ExceptionHandler[MyError, MyErrorType])`, "
            "or set an `exception_type` attribute."
        )

    exception_types = _normalize_exception_types(exception_type)

    for exc_type in exception_types:
        if not (isinstance(exc_type, type) and issubclass(exc_type, Exception)):
            raise TypeError(
                f"Exception handler {type(handler).__name__!r} declares "
                f"{exc_type!r} as an exception it handles, but that is not a "
                "subclass of `Exception`."
            )

    return exception_types


def get_error_type(handler: ExceptionHandler[Any]) -> Any:
    attribute = getattr(handler, "error_type", None)
    _, declared = _get_declared_types(type(handler))

    if attribute is not None and declared is not None and attribute != declared:
        raise TypeError(
            f"Exception handler {type(handler).__name__!r} declares conflicting "
            "GraphQL error types via its type parameter and its `error_type` "
            "attribute. Declare the error type in one place."
        )

    error_type = attribute if attribute is not None else declared

    if error_type is None:
        raise TypeError(
            f"Exception handler {type(handler).__name__!r} does not declare "
            "the GraphQL error type it returns. Parameterize the handler, e.g. "
            "`class MyHandler(strawberry.ExceptionHandler[MyError, MyErrorType])`, "
            "or set an `error_type` attribute."
        )

    return error_type


__all__ = [
    "ExceptionHandler",
    "get_error_type",
    "get_exception_types",
]
