import dataclasses
import inspect
import sys
import types
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import dataclass_transform

from .exceptions import (
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    ObjectIsNotClassError,
)
from .field import StrawberryField, field
from .type import get_object_definition
from .types.type_resolver import _get_fields
from .types.types import (
    StrawberryObjectDefinition,
)
from .utils.dataclasses import add_custom_init_fn
from .utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor
from .utils.str_converters import to_camel_case

T = TypeVar("T", bound=Type)


def _get_interfaces(cls: Type[Any]) -> List[StrawberryObjectDefinition]:
    interfaces: Dict[str, StrawberryObjectDefinition] = {}

    for base in cls.__mro__[1:]:  # Exclude current class
        type_definition = get_object_definition(base)
        if type_definition and type_definition.is_interface:
            # TODO: make this better, and add comment on why it is needed
            if existing_definition := interfaces.get(type_definition.name):
                if existing_definition.concrete_of == type_definition:
                    break

            interfaces[type_definition.name] = type_definition

    return list(interfaces.values())


def _check_field_annotations(cls: Type[Any]):
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
            # If the field has a type override then use that instead of using
            # the class annotations or resolver annotation
            if field_.type_annotation is not None:
                cls_annotations[field_name] = field_.type_annotation.annotation
                continue

            # Make sure the cls has an annotation
            if field_name not in cls_annotations:
                # If the field uses the default resolver, the field _must_ be
                # annotated
                if not field_.base_resolver:
                    raise MissingFieldAnnotationError(field_name, cls)

                # The resolver _must_ have a return type annotation
                # TODO: Maybe check this immediately when adding resolver to
                #       field
                if field_.base_resolver.type_annotation is None:
                    raise MissingReturnAnnotationError(
                        field_name, resolver=field_.base_resolver
                    )

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
            raise MissingFieldAnnotationError(field_name, cls)


def _wrap_dataclass(cls: Type[Any]):
    """Wrap a strawberry.type class with a dataclass and check for any issues
    before doing so"""

    # Ensure all Fields have been properly type-annotated
    _check_field_annotations(cls)

    dclass_kwargs: Dict[str, bool] = {}

    # Python 3.10 introduces the kw_only param. If we're on an older version
    # then generate our own custom init function
    if sys.version_info >= (3, 10):
        dclass_kwargs["kw_only"] = True
    else:
        dclass_kwargs["init"] = False

    dclass = dataclasses.dataclass(cls, **dclass_kwargs)

    if sys.version_info < (3, 10):
        add_custom_init_fn(dclass)

    return dclass


def _process_type(
    cls: Type[Any],
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
    resolve_type = getattr(cls, "resolve_type", None)

    cls.__strawberry_definition__ = StrawberryObjectDefinition(
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
        resolve_type=resolve_type,
    )

    should_add_class_getitem = is_interface and cls.__strawberry_definition__.is_generic

    # check if any field is generic
    if not any(getattr(field_.type, "is_generic", None) for field_ in fields):
        should_add_class_getitem = False

    if should_add_class_getitem:

        def __class_getitem__(cls: Type[Any], params: Any) -> Type[Any]:
            params = params if isinstance(params, tuple) else (params,)
            type_vars = (p.__name__ for p in cls.__parameters__)

            type_var_map = dict(zip(type_vars, params))

            return cls.__strawberry_definition__.copy_with(type_var_map=type_var_map)

        cls.__class_getitem__ = classmethod(__class_getitem__)

    # TODO: remove when deprecating _type_definition
    DeprecatedDescriptor(
        DEPRECATION_MESSAGES._TYPE_DEFINITION,
        cls.__strawberry_definition__,
        "_type_definition",
    ).inject(cls)

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


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def type(
    cls: T,
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> T:
    ...


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def type(
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> Callable[[T], T]:
    ...


def type(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
) -> Union[T, Callable[[T], T]]:
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    def wrap(cls: Type):
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
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    cls: T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> T:
    ...


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> Callable[[T], T]:
    ...


def input(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
):
    """Annotates a class as a GraphQL Input type.
    Example usage:
    >>> @strawberry.input
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    return type(  # type: ignore # not sure why mypy complains here
        cls,
        name=name,
        description=description,
        directives=directives,
        is_input=True,
    )


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    cls: T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> T:
    ...


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> Callable[[T], T]:
    ...


@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
):
    """Annotates a class as a GraphQL Interface.
    Example usage:
    >>> @strawberry.interface
    >>> class X:
    >>>     field_abc: str
    """

    return type(  # type: ignore # not sure why mypy complains here
        cls,
        name=name,
        description=description,
        directives=directives,
        is_interface=True,
    )


def asdict(obj: Any) -> Dict[str, object]:
    """Convert a strawberry object into a dictionary.
    This wraps the dataclasses.asdict function to strawberry.

    Example usage:
    >>> @strawberry.type
    >>> class User:
    >>>     name: str
    >>>     age: int
    >>> # should be {"name": "Lorem", "age": 25}
    >>> user_dict = strawberry.asdict(User(name="Lorem", age=25))
    """
    return dataclasses.asdict(obj)


__all__ = [
    "StrawberryObjectDefinition",
    "input",
    "interface",
    "type",
    "asdict",
]
