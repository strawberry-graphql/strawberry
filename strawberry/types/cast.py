from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, overload

from strawberry.exceptions import AmbiguousCastError
from strawberry.types.base import StrawberryObjectDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from graphql import GraphQLObjectType

    from strawberry.schema.types.concrete_type import TypeMap

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


def get_cast_type_name(
    obj: Any,
    possible_types: Iterable[GraphQLObjectType],
    type_map: TypeMap,
    field_name: str,
) -> str | None:
    """Return the name of the type in `possible_types` that `obj` is cast to.

    A cast to a generic type matches its specializations, like `IntEdge` for
    `strawberry.cast(Edge, row)`, and raises an error when it matches more than
    one. Returns `None` when `obj` isn't cast to one of the types, for example
    when it's cast to an interface.
    """
    if (type_cast := get_strawberry_type_cast(obj)) is None:
        return None

    type_names = [
        type_.name
        for type_ in possible_types
        if _is_definition_of(type_map[type_.name].definition, type_cast)
    ]

    if len(type_names) > 1:
        raise AmbiguousCastError(field_name, type_cast, type_names)

    return type_names[0] if type_names else None


def _is_definition_of(definition: object, type_: type) -> bool:
    """Whether `definition` defines the object type `type_` or a specialization of it."""
    if not isinstance(definition, StrawberryObjectDefinition):
        return False

    if definition.origin is type_:
        return True

    return definition.concrete_of is not None and definition.concrete_of.origin is type_
