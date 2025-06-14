import builtins
import dataclasses
import inspect
import sys
import types
from collections.abc import Sequence
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import dataclass_transform

from strawberry.exceptions import (
    InvalidSuperclassInterfaceError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    ObjectIsNotClassError,
)
from strawberry.types.base import get_object_definition
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor
from strawberry.utils.str_converters import to_camel_case

from .base import StrawberryObjectDefinition
from .field import StrawberryField, field
from .type_resolver import _get_fields

T = TypeVar("T", bound=builtins.type)


def _get_interfaces(cls: builtins.type[Any]) -> list[StrawberryObjectDefinition]:
    interfaces: list[StrawberryObjectDefinition] = []
    for base in cls.__mro__[1:]:  # Exclude current class
        type_definition = get_object_definition(base)
        if type_definition and type_definition.is_interface:
            interfaces.append(type_definition)

    return interfaces


def _check_field_annotations(cls: builtins.type[Any]) -> None:
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
                if field_name not in cls_annotations:
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

                if field_name not in cls_annotations:
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


def _wrap_dataclass(cls: builtins.type[T]) -> builtins.type[T]:
    """Wrap a strawberry.type class with a dataclass and check for any issues before doing so."""
    # Ensure all Fields have been properly type-annotated
    _check_field_annotations(cls)

    dclass_kwargs: dict[str, bool] = {}

    # Python 3.10 introduces the kw_only param. If we're on an older version
    # then generate our own custom init function
    if sys.version_info >= (3, 10):
        dclass_kwargs["kw_only"] = True
    else:
        dclass_kwargs["init"] = False

    dclass = dataclasses.dataclass(cls, **dclass_kwargs)

    if sys.version_info < (3, 10):
        from strawberry.utils.dataclasses import add_custom_init_fn

        add_custom_init_fn(dclass)

    return dclass


def _inject_default_for_maybe_annotations(
    cls: builtins.type[T], annotations: dict[str, Any]
) -> None:
    """Inject `= None` for fields with `Maybe` annotations and no default value."""
    for name, annotation in annotations.copy().items():
        if _annotation_is_maybe(annotation) and not hasattr(cls, name):
            setattr(cls, name, None)


def _process_type(
    cls: T,
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    extend: bool = False,
    original_type_annotations: Optional[dict[str, Any]] = None,
) -> T:
    name = name or to_camel_case(cls.__name__)
    original_type_annotations = original_type_annotations or {}

    interfaces = _get_interfaces(cls)
    fields = _get_fields(cls, original_type_annotations)
    is_type_of = getattr(cls, "is_type_of", None)
    resolve_type = getattr(cls, "resolve_type", None)

    if is_input and interfaces:
        raise InvalidSuperclassInterfaceError(
            cls=cls, input_name=name, interfaces=interfaces
        )

    cls.__strawberry_definition__ = StrawberryObjectDefinition(  # type: ignore[attr-defined]
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        interfaces=interfaces,
        description=description,
        directives=directives,
        origin=cls,
        extend=extend,
        fields=fields,
        is_type_of=is_type_of,
        resolve_type=resolve_type,
    )
    # TODO: remove when deprecating _type_definition
    DeprecatedDescriptor(
        DEPRECATION_MESSAGES._TYPE_DEFINITION,
        cls.__strawberry_definition__,  # type: ignore[attr-defined]
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
) -> T: ...


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
) -> Callable[[T], T]: ...


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

    Similar to `dataclasses.dataclass`, but with additional functionality for
    defining GraphQL types.

    Args:
        cls: The class we want to create a GraphQL type from.
        name: The name of the GraphQL type.
        is_input: Whether the class is an input type. Used internally, use `@strawerry.input` instead of passing this flag.
        is_interface: Whether the class is an interface. Used internally, use `@strawerry.interface` instead of passing this flag.
        description: The description of the GraphQL type.
        directives: The directives of the GraphQL type.
        extend: Whether the class is extending an existing type.

    Returns:
        The class.

    Example usage:

    ```python
    @strawberry.type
    class User:
        name: str = "A name"
    ```

    You can also pass parameters to the decorator:

    ```python
    @strawberry.type(name="UserType", description="A user type")
    class MyUser:
        name: str = "A name"
    ```
    """

    def wrap(cls: T) -> T:
        if not inspect.isclass(cls):
            if is_input:
                exc = ObjectIsNotClassError.input
            elif is_interface:
                exc = ObjectIsNotClassError.interface
            else:
                exc = ObjectIsNotClassError.type
            raise exc(cls)

        # when running `_wrap_dataclass` we lose some of the information about the
        # the passed types, especially the type_annotation inside the StrawberryField
        # this makes it impossible to customise the field type, like this:
        # >>> @strawberry.type
        # >>> class Query:
        # >>>     a: int = strawberry.field(graphql_type=str)
        # so we need to extract the information before running `_wrap_dataclass`
        original_type_annotations: dict[str, Any] = {}

        annotations = getattr(cls, "__annotations__", {})

        for field_name in annotations:
            field = getattr(cls, field_name, None)

            if field and isinstance(field, StrawberryField) and field.type_annotation:
                original_type_annotations[field_name] = field.type_annotation.annotation
        if is_input:
            _inject_default_for_maybe_annotations(cls, annotations)
        wrapped = _wrap_dataclass(cls)

        return _process_type(  # type: ignore
            wrapped,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            directives=directives,
            extend=extend,
            original_type_annotations=original_type_annotations,
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
    one_of: Optional[bool] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    *,
    name: Optional[str] = None,
    one_of: Optional[bool] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> Callable[[T], T]: ...


def input(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    one_of: Optional[bool] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
):
    """Annotates a class as a GraphQL Input type.

    Similar to `@strawberry.type`, but for input types.

    Args:
        cls: The class we want to create a GraphQL input type from.
        name: The name of the GraphQL input type.
        description: The description of the GraphQL input type.
        directives: The directives of the GraphQL input type.
        one_of: Whether the input type is a `oneOf` type.

    Returns:
        The class.

    Example usage:

    ```python
    @strawberry.input
    class UserInput:
        name: str
    ```

    You can also pass parameters to the decorator:

    ```python
    @strawberry.input(name="UserInputType", description="A user input type")
    class MyUserInput:
        name: str
    ```
    """
    from strawberry.schema_directives import OneOf

    if one_of:
        directives = (*(directives or ()), OneOf())

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
) -> T: ...


@overload
@dataclass_transform(
    order_default=True, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
) -> Callable[[T], T]: ...


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

    Similar to `@strawberry.type`, but for interfaces.

    Args:
        cls: The class we want to create a GraphQL interface from.
        name: The name of the GraphQL interface.
        description: The description of the GraphQL interface.
        directives: The directives of the GraphQL interface.

    Returns:
        The class.

    Example usage:

    ```python
    @strawberry.interface
    class Node:
        id: str
    ```

    You can also pass parameters to the decorator:

    ```python
    @strawberry.interface(name="NodeType", description="A node type")
    class MyNode:
        id: str
    ```
    """
    return type(  # type: ignore # not sure why mypy complains here
        cls,
        name=name,
        description=description,
        directives=directives,
        is_interface=True,
    )


def asdict(obj: Any) -> dict[str, object]:
    """Convert a strawberry object into a dictionary.

    This wraps the dataclasses.asdict function to strawberry.

    Args:
        obj: The object to convert into a dictionary.

    Returns:
        A dictionary representation of the object.

    Example usage:

    ```python
    @strawberry.type
    class User:
        name: str
        age: int


    strawberry.asdict(User(name="Lorem", age=25))
    # {"name": "Lorem", "age": 25}
    ```
    """
    return dataclasses.asdict(obj)


__all__ = [
    "StrawberryObjectDefinition",
    "asdict",
    "input",
    "interface",
    "type",
]
