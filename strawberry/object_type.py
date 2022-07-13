import dataclasses
import inspect
import types
from typing import Callable, List, Optional, Sequence, Type, TypeVar, cast, overload

from .exceptions import (
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    ObjectIsNotClassError,
)
from .field import StrawberryField, field
from .types.type_resolver import _get_fields
from .types.types import TypeDefinition
from .utils.str_converters import to_camel_case
from .utils.typing import __dataclass_transform__


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

    for field_name, field_ in cls.__dict__.items():
        if not isinstance(field_, (StrawberryField, dataclasses.Field)):
            # Not a dataclasses.Field, nor a StrawberryField. Ignore
            continue

        # If the field is a StrawberryField we need to do a bit of extra work
        # to make sure dataclasses.dataclass is ready for it
        if isinstance(field_, StrawberryField):

            # Make sure the cls has an annotation
            if field_name not in cls_annotations:
                # If the field uses the default resolver, the field _must_ be
                # annotated
                if not field_.base_resolver:
                    raise MissingFieldAnnotationError(field_name)

                # The resolver _must_ have a return type annotation
                # TODO: Maybe check this immediately when adding resolver to
                #       field
                if field_.base_resolver.type_annotation is None:
                    raise MissingReturnAnnotationError(field_name)

                cls_annotations[field_name] = field_.base_resolver.type_annotation

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
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
):
    name = name or to_camel_case(cls.__name__)

    interfaces = _get_interfaces(cls)
    fields = _get_fields(cls)
    is_type_of = getattr(cls, "is_type_of", None)

    cls._type_definition = TypeDefinition(
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        interfaces=interfaces,
        description=description,
        directives=directives,
        origin=cls,
        extend=extend,
        _fields=fields,
        is_type_of=is_type_of,
    )

    # dataclasses removes attributes from the class here:
    # https://github.com/python/cpython/blob/577d7c4e/Lib/dataclasses.py#L873-L880
    # so we need to restore them, this will change in future, but for now this
    # solution should suffice
    for field_ in fields:
        if field_.base_resolver and field_.python_name:
            wrapped_func = field_.base_resolver.wrapped_func

            # Bind the functions to the class object. This is necessary because when
            # the @strawberry.field decorator is used on @staticmethod/@classmethods,
            # we get the raw staticmethod/classmethod objects before class evaluation
            # binds them to the class. We need to do this manually.
            if isinstance(wrapped_func, staticmethod):
                bound_method = wrapped_func.__get__(cls)
                field_.base_resolver.wrapped_func = bound_method
            elif isinstance(wrapped_func, classmethod):
                bound_method = types.MethodType(wrapped_func.__func__, cls)
                field_.base_resolver.wrapped_func = bound_method

            setattr(cls, field_.python_name, wrapped_func)

    return cls


T = TypeVar("T")


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def type(
    cls: T,
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> T:
    ...


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def type(
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> Callable[[T], T]:
    ...


def type(
    cls=None,
    *,
    name=None,
    is_input=False,
    is_interface=False,
    description=None,
    directives=(),
    extend=False,
):
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    def wrap(cls):
        if not inspect.isclass(cls):
            if is_input:
                exc = ObjectIsNotClassError.input
            elif is_interface:
                exc = ObjectIsNotClassError.interface
            else:
                exc = ObjectIsNotClassError.type
            raise exc(cls)

        wrapped = _wrap_dataclass(cls)
        return _process_type(
            wrapped,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            directives=directives,
            extend=extend,
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def input(
    cls: T,
    *,
    name: str = None,
    description: str = None,
    directives: Optional[Sequence[object]] = (),
) -> T:
    ...


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def input(
    *,
    name: str = None,
    description: str = None,
    directives: Optional[Sequence[object]] = (),
) -> Callable[[T], T]:
    ...


def input(
    cls=None,
    *,
    name=None,
    description=None,
    directives=(),
):
    """Annotates a class as a GraphQL Input type.
    Example usage:
    >>> @strawberry.input:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    return type(
        cls, name=name, description=description, directives=directives, is_input=True
    )


@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def interface(
    cls: Type = None,
    *,
    name: str = None,
    description: str = None,
    directives: Optional[Sequence[object]] = (),
):
    """Annotates a class as a GraphQL Interface.
    Example usage:
    >>> @strawberry.interface:
    >>> class X:
    >>>     field_abc: str
    """

    return type(
        cls,
        name=name,
        description=description,
        directives=directives,
        is_interface=True,
    )


__all__ = [
    "TypeDefinition",
    "input",
    "interface",
    "type",
]
