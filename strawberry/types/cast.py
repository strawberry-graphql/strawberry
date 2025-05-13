from __future__ import annotations

from typing import Any, TypeVar, overload

_T = TypeVar("_T", bound=object)

TYPE_CAST_ATTRIBUTE = "__as_strawberry_type__"


@overload
def cast(type_: type, obj: None) -> None: ...


@overload
def cast(type_: type, obj: _T) -> _T: ...


def cast(type_: type, obj: _T | None) -> _T | None:
    """Cast an object to given type.

    This is used to mark an object as a cast object, so that the type can be
    picked up when resolving unions/interfaces in case of ambiguity, which can
    happen when returning an alike object instead of an instance of the type
    (e.g. returning a Django, Pydantic or SQLAlchemy object)
    """
    if obj is None:
        return None

    setattr(obj, TYPE_CAST_ATTRIBUTE, type_)
    return obj


def get_strawberry_type_cast(obj: Any) -> type | None:
    """Get the type of a cast object."""
    return getattr(obj, TYPE_CAST_ATTRIBUTE, None)
