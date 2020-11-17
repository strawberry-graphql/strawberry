import dataclasses
from functools import partial
from typing import List, Optional, Type, cast

from strawberry.utils.typing import is_generic

from .exceptions import MissingFieldAnnotationError, MissingReturnAnnotationError
from .field import StrawberryField
from .types.type_resolver import _get_fields
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

        for inherited_interface in _get_interfaces(base):
            interfaces.append(inherited_interface)

    return interfaces


def _check_field_annotations(cls: Type):
    """Are any of the dataclass Fields missing type annotations?

    This is similar to the check that dataclasses do during creation, but allows us to
    manually add fields to cls' __annotations__ or raise proper Strawberry exceptions if
    necessary

    https://github.com/python/cpython/blob/6fed3c85402c5ca704eb3f3189ca3f5c67a08d19/Lib/dataclasses.py#L881-L884
    """
    cls_annotations = cls.__dict__.get("__annotations__", {})
    cls.__annotations__ = cls_annotations

    for field_name, field in cls.__dict__.items():
        if not isinstance(field, (StrawberryField, dataclasses.Field)):
            # Not a dataclasses.Field, nor a StrawberryField. Ignore
            continue

        # If the field is a StrawberryField we need to do a bit of extra work
        # to make sure dataclasses.dataclass is ready for it
        if isinstance(field, StrawberryField):

            field_definition = field._field_definition

            # Make sure the cls has an annotation
            if field_name not in cls_annotations:
                # If the field uses the default resolver, the field _must_ be
                # annotated
                if not field_definition.base_resolver:
                    raise MissingFieldAnnotationError(field_name)

                # The resolver _must_ have a return type annotation
                # TODO: Maybe check this immediately when adding resolver to
                #       field
                if field_definition.base_resolver.type is None:
                    raise MissingReturnAnnotationError(field_name)

                cls_annotations[field_name] = field_definition.base_resolver.type

            # TODO: Make sure the cls annotation agrees with the field's type
            # >>> if cls_annotations[field_name] != field.base_resolver.type:
            # >>>     # TODO: Proper error
            # >>>    raise Exception

        # If somehow a non-StrawberryField field is added to the cls without annotations
        # it raises an exception. This would occur if someone manually uses
        # dataclasses.field
        if field_name not in cls_annotations:
            # Field object exists but did not get an annotation
            raise MissingFieldAnnotationError(field_name)


def _wrap_dataclass(cls: Type):
    """Wrap a strawberry.type class with a dataclass and check for any issues
    before doing so"""

    # Ensure all Fields have been properly type-annotated
    _check_field_annotations(cls)

    return dataclasses.dataclass(cls)


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

    wrapped = _wrap_dataclass(cls)

    interfaces = _get_interfaces(wrapped)
    fields = _get_fields(cls)

    wrapped._type_definition = TypeDefinition(
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        is_generic=is_generic(cls),
        interfaces=interfaces,
        description=description,
        federation=federation or FederationTypeParams(),
        origin=cls,
        _fields=fields,
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


__all__ = [
    "FederationTypeParams",
    "TypeDefinition",
    "input",
    "interface",
    "type",
]
