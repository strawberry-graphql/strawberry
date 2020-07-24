import dataclasses
from functools import partial
from typing import List, Optional, Type, cast

from strawberry.utils.typing import is_generic

from .types.types import FederationTypeParams, TypeDefinition
from .utils.str_converters import to_camel_case


def _get_interfaces(cls: Type) -> List[TypeDefinition]:
    interfaces = []

    for base in cls.__bases__:
        type_definition = cast(
            Optional[TypeDefinition], getattr(base, "_type_definition", None)
        )

        if type_definition and type_definition.is_interface:
            interfaces.append(type_definition)

    return interfaces


def _process_type(
    cls,
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    federation: Optional[FederationTypeParams] = None
):
    name = name or to_camel_case(cls.__name__)

    wrapped = dataclasses.dataclass(cls)

    interfaces = _get_interfaces(wrapped)

    wrapped._type_definition = TypeDefinition(
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        is_generic=is_generic(cls),
        interfaces=interfaces,
        description=description,
        federation=federation or FederationTypeParams(),
        origin=cls,
    )

    return wrapped


def type(
    cls: Type = None,
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    federation: Optional[FederationTypeParams] = None
):
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    def wrap(cls):
        return _process_type(
            cls,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            federation=federation,
        )

    if cls is None:
        return wrap

    return wrap(cls)


input = partial(type, is_input=True)
interface = partial(type, is_interface=True)
