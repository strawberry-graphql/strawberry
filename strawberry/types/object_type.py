import ast
import builtins
import copy
import dataclasses
import inspect
import sys
from collections.abc import Callable, Sequence
from typing import (
    Annotated,
    Any,
    ForwardRef,
    TypeVar,
    cast,
    get_args,
    get_origin,
    overload,
)
from typing_extensions import (
    Format,
    dataclass_transform,
    evaluate_forward_ref,
    get_annotations,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidSuperclassInterfaceError,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    MultipleStrawberryFieldsError,
    ObjectIsNotClassError,
    ResolverFieldOnInputError,
    UnresolvedStrawberryFieldError,
)
from strawberry.types.maybe import Some, _annotation_is_maybe
from strawberry.types.unset import UNSET
from strawberry.utils.str_converters import to_camel_case

from .base import StrawberryObjectDefinition, has_object_definition
from .field import StrawberryField, field, get_annotated_field
from .type_resolver import _get_fields
from .unresolved_annotations import (
    find_unresolved_options,
    get_annotated_metadata,
    get_undefined_option_names,
)

T = TypeVar("T", bound=builtins.type)


def _check_unresolved_annotation(
    cls: builtins.type, field_name: str, annotation: str, namespace: dict[str, Any]
) -> None:
    """Fail when the `strawberry.field()` options of an annotation can't be read.

    Before Python 3.14, an annotation that uses names that aren't defined yet,
    like a type defined further down the module, can't be evaluated when the
    type is created. Its type is resolved when the schema is built, but the
    options of a `strawberry.field()` in it, like permissions, would silently be
    ignored, so this fails instead, including when an item of `Annotated` can't
    be evaluated, as it could be a field.
    """
    unresolved = find_unresolved_options(
        annotation, namespace, cls=cls, field_name=field_name
    )

    if unresolved is not None:
        raise UnresolvedStrawberryFieldError(
            field_name=field_name,
            cls=cls,
            undefined_names=unresolved.undefined_names,
            in_options=unresolved.in_options,
        )


def _check_field_options(
    cls: builtins.type, field_name: str, annotation: str, namespace: dict[str, Any]
) -> None:
    """Fail when the options in an annotation use names that aren't defined yet.

    Python 3.14 evaluates annotations partially, so a `strawberry.field()` in an
    annotation is created even when its options use names that aren't defined
    yet, like a permission class defined after the type, and they get forward
    references instead.
    """
    try:
        expression = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return

    undefined_names = get_undefined_option_names(
        get_annotated_metadata(expression, namespace) or [], namespace
    )

    if undefined_names:
        raise UnresolvedStrawberryFieldError(
            field_name=field_name,
            cls=cls,
            undefined_names=sorted(undefined_names),
            in_options=True,
        )


def _process_annotated_fields(cls: T) -> dict[str, StrawberryAnnotation]:
    """Make StrawberryFields in Annotated available to dataclasses."""
    module_namespace = sys.modules[cls.__module__].__dict__
    type_annotations: dict[str, StrawberryAnnotation] = {}

    annotations = get_annotations(cls, format=Format.FORWARDREF)

    for field_name, raw_annotation in annotations.items():
        annotation: object
        if isinstance(raw_annotation, str):
            try:
                annotation = evaluate_forward_ref(
                    ForwardRef(raw_annotation),
                    owner=cls,
                    globals=module_namespace,
                    locals=dict(vars(cls)),
                    format=Format.FORWARDREF,
                )
                if isinstance(annotation, ForwardRef):
                    annotation = StrawberryAnnotation(
                        raw_annotation,
                        namespace=module_namespace,
                    ).evaluate()
            except (NameError, TypeError):
                try:
                    # like when the schema is built, e.g. for a quoted type with
                    # `strawberry.lazy()`, or a field named like the type it uses
                    annotation = StrawberryAnnotation(
                        raw_annotation,
                        namespace=module_namespace,
                    ).evaluate()
                except (NameError, TypeError):
                    # the type is resolved when the schema is built, but the
                    # options of a `strawberry.field()` in it would be lost
                    _check_unresolved_annotation(
                        cls, field_name, raw_annotation, module_namespace
                    )
                    continue
        else:
            annotation = raw_annotation

        field_type, source_field = get_annotated_field(
            annotation, cls=cls, field_name=field_name
        )

        if source_field is None:
            continue

        # e.g. `Annotated[int, strawberry.field()]` with `= strawberry.field()`
        if isinstance(cls.__dict__.get(field_name), StrawberryField):
            raise MultipleStrawberryFieldsError(field_name=field_name, cls=cls)

        if isinstance(raw_annotation, str):
            _check_field_options(
                cls, field_name, raw_annotation, {**module_namespace, **vars(cls)}
            )

        field = copy.copy(source_field)

        default = cls.__dict__.get(field_name, dataclasses.MISSING)
        if (
            field.default is dataclasses.MISSING
            and field.default_factory is dataclasses.MISSING
            and default is not dataclasses.MISSING
        ):
            if isinstance(default, dataclasses.Field):
                field.default = default.default
                field.default_factory = default.default_factory
                if default.default is not dataclasses.MISSING:
                    field.default_value = default.default
                elif callable(default.default_factory):
                    field.default_value = default.default_factory()
            else:
                field.default = default
                field.default_value = default

        if field.type_annotation is not None:
            # `graphql_type=...` replaces the type, but not the rest of the metadata
            graphql_type = field.type_annotation.raw_annotation
            field_type = (
                Annotated[(graphql_type, *get_args(field_type)[1:])]
                if get_origin(field_type) is Annotated
                else graphql_type
            )

        # a new annotation for each class, as the `strawberry.field()` can be
        # shared by several classes, e.g. through a type alias, and each class
        # resolves its type, like `graphql_type="Foo"`, in its own module, even
        # if something else set the namespace of the shared annotation
        type_annotation = StrawberryAnnotation(field_type, namespace=module_namespace)
        field.type_annotation = type_annotation

        setattr(cls, field_name, field)
        type_annotations[field_name] = type_annotation

    return type_annotations


def _get_interfaces(cls: builtins.type[Any]) -> list[StrawberryObjectDefinition]:
    interfaces: list[StrawberryObjectDefinition] = []
    for base in cls.__mro__[1:]:  # Exclude current class
        # Only use the definitions of the bases themselves, as an undecorated
        # subclass of an interface inherits its definition
        type_definition = getattr(base, "__strawberry_definition__", None)
        if (
            isinstance(type_definition, StrawberryObjectDefinition)
            and type_definition.origin is base
            and type_definition.is_interface
        ):
            interfaces.append(type_definition)

    return interfaces


def _check_field_annotations(cls: builtins.type[Any]) -> set[str]:
    """Are any of the dataclass Fields missing type annotations?

    This is similar to the check that dataclasses do during creation, but allows us to
    manually add fields to cls' __annotations__ or raise proper Strawberry exceptions if
    necessary

    Returns the names of the annotations added for fields with a resolver, which
    are only needed while the dataclass is created.

    https://github.com/python/cpython/blob/6fed3c85402c5ca704eb3f3189ca3f5c67a08d19/Lib/dataclasses.py#L881-L884
    """
    cls_annotations = get_annotations(cls)
    # TODO: do we need this?
    cls.__annotations__ = cls_annotations
    added: set[str] = set()

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
                    added.add(field_name)
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
                    # Distinguish @strawberry.field decorator from explicit
                    # strawberry.field(resolver=fn) assignment.
                    resolver_qualname = getattr(
                        field_.base_resolver.wrapped_func, "__qualname__", ""
                    )
                    if resolver_qualname != f"{cls.__qualname__}.{field_name}":
                        raise MissingFieldAnnotationError(field_name, cls)
                    raise MissingReturnAnnotationError(
                        field_name, resolver=field_.base_resolver
                    )

                if field_name not in cls_annotations:
                    cls_annotations[field_name] = field_.base_resolver.type_annotation
                    added.add(field_name)

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

    return added


def _wrap_dataclass(cls: T) -> T:
    """Wrap a strawberry.type class with a dataclass and check for any issues before doing so."""
    annotated_field_types = _process_annotated_fields(cls)

    # Ensure all Fields have been properly type-annotated
    added_annotations = _check_field_annotations(cls)
    wrapped = cast("T", dataclasses.dataclass(kw_only=True)(cls))

    # The annotations added for fields with a resolver are only for dataclasses,
    # which has its fields now. Other tools that read the class's annotations,
    # like Pydantic for a model that extends the type, would see the resolver's
    # `StrawberryAnnotation` as the type of an attribute
    for field_name in added_annotations:
        del wrapped.__annotations__[field_name]

    # dataclasses replaces each StrawberryField's type with the class annotation.
    # Restore the type with only the StrawberryField metadata removed, keeping any
    # other Annotated metadata and explicit graphql_type override intact.
    for field_name, type_annotation in annotated_field_types.items():
        wrapped.__dataclass_fields__[field_name].type_annotation = type_annotation  # type: ignore[attr-defined]

    return wrapped


def _inject_default_for_maybe_annotations(cls: T, annotations: dict[str, Any]) -> None:
    """Inject `= None` for fields with `Maybe` annotations and no default value."""
    for name, annotation in annotations.copy().items():
        if _annotation_is_maybe(annotation):
            if not hasattr(cls, name):
                setattr(cls, name, None)
            elif (
                isinstance(attr := getattr(cls, name), StrawberryField)
                and attr.default is dataclasses.MISSING
                and attr.default_factory is dataclasses.MISSING
            ):
                attr.default = None


def _get_base_with_field(
    cls: builtins.type, strawberry_field: StrawberryField
) -> builtins.type | None:
    """Return the first base type that has `strawberry_field`, if it's inherited."""
    return next(
        (
            base
            for base in cls.__mro__[1:]
            if has_object_definition(base)
            and any(
                base_field is strawberry_field
                for base_field in base.__strawberry_definition__.fields
            )
        ),
        None,
    )


def _process_type(
    cls: T,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
    original_type_annotations: dict[str, Any] | None = None,
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

    if is_input:
        dataclass_fields = {field_.name: field_ for field_ in dataclasses.fields(cls)}

        for field_ in fields:
            # a field with a resolver isn't an argument of the input's `__init__`,
            # so requests using the input would fail, and the resolver would never
            # run. An inherited field hidden with `strawberry.Private` isn't one of
            # the class's fields anymore, so it's left alone
            if (
                field_.base_resolver is not None
                and dataclass_fields.get(field_.python_name) is field_
            ):
                raise ResolverFieldOnInputError(
                    field_name=field_.python_name,
                    cls=cls,
                    resolver_field=field_,
                    inherited_from=_get_base_with_field(cls, field_),
                )

    definition = StrawberryObjectDefinition(
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
    cls.__strawberry_definition__ = definition  # type: ignore[attr-defined]

    for index, field_ in enumerate(definition.fields):
        resolver = field_.base_resolver
        if resolver is None or not field_.python_name:
            continue

        bound_resolver = resolver.bind(cls)
        if bound_resolver is not resolver:
            # The classmethod resolver is bound to another type using the field,
            # like the parent this type inherits it from, so this type gets its
            # own copy of the field
            field_copy = copy.copy(field_)
            field_copy.base_resolver = bound_resolver
            definition.fields[index] = field_copy

        # dataclasses removes attributes from the class here:
        # https://github.com/python/cpython/blob/577d7c4e/Lib/dataclasses.py#L873-L880
        # so we need to restore them, this will change in future, but for now this
        # solution should suffice. Staticmethods and classmethods are restored as
        # they were defined, so that Python binds them for subclasses and instances
        attribute = bound_resolver._descriptor
        if attribute is None:
            attribute = bound_resolver.wrapped_func

        setattr(cls, field_.python_name, attribute)

    return cls


@overload
@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def type(
    cls: T,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
) -> T: ...


@overload
@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def type(
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
) -> Callable[[T], T]: ...


@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def type(
    cls: T | None = None,
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    extend: bool = False,
) -> T | Callable[[T], T]:
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

        return _process_type(
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
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    cls: T,
    *,
    name: str | None = None,
    one_of: bool | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    *,
    name: str | None = None,
    one_of: bool | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> Callable[[T], T]: ...


@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def input(
    cls: T | None = None,
    *,
    name: str | None = None,
    one_of: bool | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
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
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    cls: T,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> Callable[[T], T]: ...


@dataclass_transform(
    order_default=False, kw_only_default=True, field_specifiers=(field, StrawberryField)
)
def interface(
    cls: T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
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


def _prepare(obj: Any) -> Any:
    """Recursively unwrap Some() instances so dataclasses.asdict can process the result."""
    if isinstance(obj, Some):
        # Unwrap that Some container
        return _prepare(obj.value)

    if dataclasses.is_dataclass(obj) and not isinstance(obj, builtins.type):
        hints = get_annotations(builtins.type(obj))
        # Intentionally avoiding the similar `dataclasses.replace` here,
        # which calls `__init__` (and therefore `__post_init__`).
        # That may trigger unintended side effects, and it rejects `init=False` fields
        # in its changes dict. A shallow `copy.copy` sidesteps both issues:
        # it duplicates the instance without invoking any initialisation logic.
        obj_copy = copy.copy(obj)
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            if value is None and _annotation_is_maybe(hints.get(f.name)):
                value = UNSET
            else:
                value = _prepare(value)
            # `object.__setattr__` bypasses the frozen dataclass override of
            # `__setattr__` (which raises `FrozenInstanceError`), writing
            # directly to the instance. This is the same approach used by
            # `dataclasses.replace` internally.
            object.__setattr__(obj_copy, f.name, value)
        return obj_copy

    # Recurse into lists, tuples, namedtuples, and dicts to prepare their values.
    # Defensively filter out the `UNSET` value at each level, as well.
    if isinstance(obj, (list, tuple)):
        # NOTE namedtuples are also included in this case.
        # If more specific handling is needed for a namedtuple, check for
        # `hasattr(obj, "_fields")` later.
        return builtins.type(obj)(_prepare(v) for v in obj if v is not UNSET)
    if isinstance(obj, dict):
        return {k: _prepare(v) for k, v in obj.items() if v is not UNSET}

    # obj is none of the above instances -> return unchanged
    return obj


def _asdict_dict_factory(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """dict_factory for dataclasses.asdict that excludes UNSET values."""
    return {k: v for k, v in items if v is not UNSET}


def asdict(obj: Any) -> dict[str, object]:
    """Convert a strawberry object into a dictionary.

    This wraps the ``dataclasses.asdict`` function to strawberry,
    while handling some special cases that ``dataclasses.asdict`` does not:

    - ``UNSET`` fields are excluded.
    - ``Some(value)`` containers are unwrapped, returning their ``value`` only.

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
    return dataclasses.asdict(_prepare(obj), dict_factory=_asdict_dict_factory)


__all__ = [
    "StrawberryObjectDefinition",
    "asdict",
    "input",
    "interface",
    "type",
]
