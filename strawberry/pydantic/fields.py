"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import datetime
import math
import sys
import types
import uuid
from collections import abc
from decimal import Decimal
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ForwardRef,
    Optional,
    Union,
    get_args,
    get_origin,
)
from typing_extensions import Format, get_annotations

import pydantic
import pydantic_core
from graphql.type.directives import DEFAULT_DEPRECATION_REASON
from pydantic import (
    AwareDatetime,
    BaseModel,
    FutureDate,
    FutureDatetime,
    NaiveDatetime,
    PastDate,
    PastDatetime,
    RootModel,
)
from pydantic_core import PydanticUndefined

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.file_uploads import Upload
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, _contains_strawberry_field
from strawberry.types.lazy_type import StrawberryLazyReference, lazy
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.types.private import StrawberryPrivate, is_private
from strawberry.types.union import StrawberryUnion, union
from strawberry.utils.typing import is_union

from .exceptions import (
    MaybeFieldError,
    PydanticFieldWithoutResolverError,
    ResolverFieldOnInputError,
    ResolverFieldOverridesModelFieldError,
    StrawberryFieldAsDefaultError,
    UnregisteredPydanticTypeError,
    UnresolvedAnnotatedFieldError,
    UnsupportedRootModelError,
    UploadFieldError,
)
from .resolver_field import get_resolver_field, is_field_decorator

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from pydantic.fields import FieldInfo

    from strawberry.types.base import StrawberryType


def _is_new_type(annotation: object) -> bool:
    return callable(annotation) and hasattr(annotation, "__supertype__")


class _UnregisteredModel(Exception):
    def __init__(self, model: type[BaseModel]) -> None:
        self.model = model


def _is_subclass(annotation: object, base: type) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(annotation, base)
    except TypeError:
        # e.g. generic aliases like `list[int]`, which are types on python 3.10
        return False


def _get_field_origins(cls: type[BaseModel]) -> dict[str, type]:
    """Map each annotated name to the class in the MRO that declares it."""
    origins: dict[str, type] = {}

    for base in cls.__mro__:
        for name in get_annotations(base, format=Format.FORWARDREF):
            origins.setdefault(name, base)

    return origins


def _get_strawberry_base_field(origin: type, field_name: str) -> StrawberryField | None:
    """Return the field declared on a regular Strawberry type or interface.

    Pydantic collects fields declared on non-pydantic bases too, but it doesn't
    know about their `strawberry.field()` configuration (e.g. permissions), so we
    reuse the Strawberry field, like `@strawberry.type` does for its bases.
    """
    if issubclass(origin, BaseModel):
        return None

    # only the class's own definition, not one inherited from its bases
    definition = vars(origin).get("__strawberry_definition__")

    if not isinstance(definition, StrawberryObjectDefinition):
        return None

    return next(
        (field for field in definition.fields if field.python_name == field_name),
        None,
    )


def _get_annotated_metadata(annotation: object) -> Iterator[object]:
    """Yield the metadata of the `Annotated` types in `annotation`, at any depth."""
    if get_origin(annotation) is Annotated:
        annotation, *metadata = get_args(annotation)

        yield from metadata
        yield from _get_annotated_metadata(annotation)
    else:
        for arg in get_args(annotation):
            yield from _get_annotated_metadata(arg)


_TYPE_METADATA = (StrawberryLazyReference, StrawberryPrivate, StrawberryUnion)


def _lookup(node: ast.expr, namespace: dict[str, Any]) -> object:
    """Return the value of a name like `Hidden` or `strawberry.lazy`, if any."""
    if isinstance(node, ast.Name):
        return namespace.get(node.id)

    if isinstance(node, ast.Attribute):
        return getattr(_lookup(node.value, namespace), node.attr, None)

    return None


def _has_annotated_options(node: ast.AST, namespace: dict[str, Any]) -> bool:
    """Return whether `node` is an `Annotated` type with options for the field.

    `strawberry.lazy()`, `strawberry.union()` and `strawberry.Private` aren't
    options: Strawberry reads them from the type when it resolves it.
    """
    if isinstance(node, ast.Subscript) and (
        getattr(node.value, "id", None) == "Annotated"
        or getattr(node.value, "attr", None) == "Annotated"
        or _lookup(node.value, namespace) is Annotated
    ):
        # e.g. `Annotated[Account, strawberry.lazy("app.accounts")]`
        metadata = node.slice.elts[1:] if isinstance(node.slice, ast.Tuple) else []

        return not all(
            isinstance(item, ast.Call)
            and _lookup(item.func, namespace) in (lazy, union)
            for item in metadata
        )

    # an alias, e.g. `Hidden = Annotated[T, pydantic.Field(exclude=True)]`
    return isinstance(node, (ast.Name, ast.Attribute)) and any(
        not isinstance(item, _TYPE_METADATA)
        for item in _get_annotated_metadata(_lookup(node, namespace))
    )


def _check_annotated_is_resolved(
    annotation: object, *, cls: type, model: type, field_name: str
) -> None:
    """Fail when pydantic couldn't read the `Annotated` options of a field yet.

    Pydantic keeps an annotation that uses names that aren't defined yet, like a
    model defined further down the module, as a string, and only reads its
    `Annotated` metadata once the model is rebuilt. Strawberry reads the field
    when the model is decorated, so options like the permissions of
    `strawberry.field()` or `Field(exclude=True)` would silently be lost.
    """
    if isinstance(annotation, ForwardRef):
        annotation = annotation.__forward_arg__

    if not isinstance(annotation, str):
        return

    try:
        tree = ast.parse(annotation, mode="eval")
    except SyntaxError:
        return

    module = sys.modules.get(cls.__module__)
    namespace = vars(module) if module is not None else {}

    if any(_has_annotated_options(node, namespace) for node in ast.walk(tree)):
        raise UnresolvedAnnotatedFieldError(field_name=field_name, cls=cls, model=model)


def _get_strawberry_field_override(
    field_info: FieldInfo, cls: type, field_name: str, *, model: type
) -> StrawberryField | None:
    """Return the `strawberry.field()` from `Annotated[T, strawberry.field()]`.

    `cls` is the class that declares the field, and `model` the decorated model.
    """
    # Pydantic treats a `strawberry.field()` assigned as the default like a
    # dataclass field: it keeps its default and discards everything else. The
    # original object is only kept on a private attribute, so this check is best
    # effort.
    if isinstance(getattr(field_info, "_original_assignment", None), StrawberryField):
        raise StrawberryFieldAsDefaultError(field_name=field_name, cls=cls)

    _check_annotated_is_resolved(
        field_info.annotation, cls=cls, model=model, field_name=field_name
    )

    # `strawberry.pydantic.field` is only for fields with a resolver
    if is_field_decorator(field_info.default) or any(
        is_field_decorator(item)
        for item in (
            *field_info.metadata,
            *_get_annotated_metadata(field_info.annotation),
        )
    ):
        raise PydanticFieldWithoutResolverError(field_name=field_name, cls=cls)

    if _contains_strawberry_field(field_info.annotation):
        raise InvalidStrawberryFieldAnnotationError(field_name=field_name, cls=cls)

    strawberry_fields = [
        item for item in field_info.metadata if isinstance(item, StrawberryField)
    ]

    if len(strawberry_fields) > 1:
        raise MultipleStrawberryFieldsError(field_name=field_name, cls=cls)

    return strawberry_fields[0] if strawberry_fields else None


def _contains_upload(annotation: object) -> bool:
    return annotation is Upload or any(
        _contains_upload(arg) for arg in get_args(annotation)
    )


# pydantic types that only add validation to a date or datetime
_CONSTRAINED_DATE_TYPES: dict[type, type] = {
    AwareDatetime: datetime.datetime,
    NaiveDatetime: datetime.datetime,
    PastDatetime: datetime.datetime,
    FutureDatetime: datetime.datetime,
    PastDate: datetime.date,
    FutureDate: datetime.date,
}

# pydantic types exposed with the GraphQL type of their python equivalent
_PYDANTIC_TYPES: dict[type, type] = {
    pydantic.EmailStr: str,
    pydantic.SecretStr: str,
    pydantic.SecretBytes: bytes,
    pydantic.AnyUrl: str,
    pydantic.AnyHttpUrl: str,
    pydantic.HttpUrl: str,
    pydantic.PostgresDsn: str,
    pydantic.RedisDsn: str,
    pydantic_core.MultiHostUrl: str,
}

# GraphQL's Int is a 32-bit integer
_GRAPHQL_INT_RANGE = range(-(2**31), 2**31)
_CONSTANT_TYPES = (
    str,
    bool,
    Decimal,
    datetime.date,
    datetime.datetime,
    datetime.time,
    uuid.UUID,
)


def _is_constant_of_type(value: object, annotation: Any) -> bool:
    """Return whether `value` is a constant of the field type `annotation`.

    Values pydantic would have to convert first, like a string default for a
    date field, aren't constants of the field type.
    """
    if _is_new_type(annotation):
        # e.g. `strawberry.ID` and scalars registered with `scalar_map`
        return _is_constant_of_type(value, annotation.__supertype__)

    if isinstance(annotation, type) and annotation in _CONSTRAINED_DATE_TYPES:
        return _is_constant_of_type(value, _CONSTRAINED_DATE_TYPES[annotation])

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        return _is_constant_of_type(value, args[0])

    if is_union(annotation):
        types = [arg for arg in args if arg is not type(None)]

        return len(types) == 1 and _is_constant_of_type(value, types[0])

    # bare `typing.List` and `typing.Sequence` don't have an item type
    if args and (
        origin in (list, abc.Sequence) or (origin is tuple and args[1:] == (Ellipsis,))
    ):
        # GraphQL passes lists, which pydantic keeps as they are for sequences, so
        # a tuple default of a sequence would reach resolvers as a list
        containers = list if origin is abc.Sequence else (list, tuple)

        return isinstance(value, containers) and all(
            _is_constant_of_type(item, args[0]) for item in value
        )

    if _is_subclass(annotation, Enum):
        return isinstance(value, annotation)

    if annotation is int:
        return type(value) is int and value in _GRAPHQL_INT_RANGE

    if annotation is float:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    return annotation in _CONSTANT_TYPES and type(value) is annotation


def _get_graphql_default(field_info: FieldInfo) -> object:
    """Return the default to publish in the GraphQL schema for an input field.

    graphql-core fills in published defaults before pydantic validates the
    input, so a field with a published default always ends up in
    `model_fields_set`. Only constants of the field's type are published, as
    they're part of the API. `None` defaults, default factories and other values
    are applied by pydantic, so that `model_dump(exclude_unset=True)` only
    contains what the client sent and factories run for every request.
    """
    if field_info.default_factory is not None or not _is_constant_of_type(
        field_info.default, field_info.annotation
    ):
        return dataclasses.MISSING

    return field_info.default


def _set_input_default(field: StrawberryField, field_info: FieldInfo) -> None:
    default = _get_graphql_default(field_info)

    # `StrawberryField.__copy__` builds `default_value` from `default`
    field.default = default
    field.default_factory = dataclasses.MISSING
    field.default_value = default

    # input fields can only be omitted when they're nullable or have a default,
    # so fields whose default is applied by pydantic become nullable
    if default is dataclasses.MISSING and not field_info.is_required():
        assert field.type_annotation is not None

        field.type_annotation = StrawberryAnnotation(
            Optional[field.type_annotation.raw_annotation],  # noqa: UP045
            namespace=field.type_annotation.namespace,
        )


def _replace_pydantic_types(type_: Any, model: type[BaseModel]) -> Any:
    """Replace the pydantic types in `type_` with the types used by Strawberry.

    NewTypes are kept: they're resolved by the schema's scalar registry, like with
    `@strawberry.type`. That's how `strawberry.ID`, `JSON`, `Upload` and
    `scalar_map` scalars work.
    """
    if isinstance(type_, type):
        type_ = _CONSTRAINED_DATE_TYPES.get(type_, type_)
        type_ = _PYDANTIC_TYPES.get(type_, type_)

    if _is_subclass(type_, BaseModel):
        # `model` can reference itself, but it's only registered after its fields
        if type_ is model or hasattr(type_, "__strawberry_definition__"):
            return type_

        raise _UnregisteredModel(type_)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return type_

    args = tuple(_replace_pydantic_types(arg, model) for arg in get_args(type_))

    if is_union(type_):
        # `X | Y` can't be subscripted, and on python 3.10 forward references
        # don't support `|`
        return Union[args]  # noqa: UP007

    return origin[args]


def _with_strawberry_metadata(annotation: Any, metadata: Iterable[object]) -> Any:
    """Add back the Strawberry metadata of `Annotated`.

    Pydantic keeps the metadata of a field's `Annotated` apart from its type, but
    the type needs `strawberry.union()`, and `strawberry.lazy()` to resolve a
    quoted type from another module.
    """
    strawberry_metadata = [
        item
        for item in metadata
        if isinstance(item, (StrawberryUnion, StrawberryLazyReference))
    ]

    if not strawberry_metadata:
        return annotation

    return Annotated[(annotation, *strawberry_metadata)]


def _get_computed_field_annotation(
    cls: type[BaseModel], origin: type, field_name: str
) -> tuple[Any, StrawberryField | None]:
    """Return the type of a computed field and its `strawberry.field()`, if any."""
    computed_field_info = cls.model_computed_fields[field_name]
    annotation = computed_field_info.return_type

    if annotation is PydanticUndefined:
        # pydantic couldn't resolve a forward reference yet, Strawberry resolves
        # the annotation when the schema is built
        wrapped_property = computed_field_info.wrapped_property
        getter = (
            wrapped_property.fget
            if isinstance(wrapped_property, property)
            else wrapped_property.func
        )
        annotation = get_annotations(getter, format=Format.FORWARDREF)["return"]
        _check_annotated_is_resolved(
            annotation, cls=origin, model=cls, field_name=field_name
        )

    # `strawberry.pydantic.field` is only for fields with a resolver
    if any(is_field_decorator(item) for item in _get_annotated_metadata(annotation)):
        raise PydanticFieldWithoutResolverError(field_name=field_name, cls=origin)

    if get_origin(annotation) is not Annotated:
        return annotation, None

    annotation, *metadata = get_args(annotation)
    strawberry_fields = [item for item in metadata if isinstance(item, StrawberryField)]

    if len(strawberry_fields) > 1:
        raise MultipleStrawberryFieldsError(field_name=field_name, cls=origin)

    return (
        _with_strawberry_metadata(annotation, metadata),
        strawberry_fields[0] if strawberry_fields else None,
    )


def _create_strawberry_field(
    cls: type[BaseModel],
    origin: type,
    field_name: str,
    field_info: FieldInfo | None,
    *,
    is_input: bool,
) -> StrawberryField:
    # computed fields don't have a FieldInfo
    if field_info is not None:
        annotation = _with_strawberry_metadata(
            field_info.annotation, field_info.metadata
        )
        description = field_info.description
        strawberry_override = _get_strawberry_field_override(
            field_info, origin, field_name, model=cls
        )
    else:
        annotation, strawberry_override = _get_computed_field_annotation(
            cls, origin, field_name
        )
        description = cls.model_computed_fields[field_name].description

    # Start from the user's `strawberry.field()`, so all of its options are
    # kept, and fill in what pydantic knows about the field
    strawberry_field = (
        copy.copy(strawberry_override)
        if strawberry_override is not None
        else StrawberryField()
    )
    # pydantic aliases describe the model's own (de)serialization, so like with
    # `@strawberry.type` the GraphQL name comes from the python name, unless set
    # with `strawberry.field(name=...)`
    strawberry_field.python_name = field_name
    strawberry_field.origin = cls

    if strawberry_field.description is None:
        strawberry_field.description = description

    deprecated_field_info = (
        field_info
        if field_info is not None
        else cls.model_computed_fields.get(field_name)
    )

    # GraphQL doesn't allow deprecating required input fields, and deprecated
    # input fields are hidden by default in introspection, so only fields of
    # output types are deprecated
    if (
        not is_input
        and strawberry_field.deprecation_reason is None
        and deprecated_field_info is not None
        and deprecated_field_info.deprecated
    ):
        strawberry_field.deprecation_reason = (
            DEFAULT_DEPRECATION_REASON
            if deprecated_field_info.deprecated is True
            else deprecated_field_info.deprecation_message
        )

    if strawberry_field.type_annotation is None:
        module = sys.modules.get(origin.__module__)

        try:
            field_type = _replace_pydantic_types(annotation, model=cls)
        except _UnregisteredModel as exc:
            if issubclass(exc.model, RootModel):
                raise UnsupportedRootModelError(
                    exc.model, cls=origin, field_name=field_name
                ) from None

            raise UnregisteredPydanticTypeError(
                exc.model, cls=origin, field_name=field_name, is_input=is_input
            ) from None

        strawberry_field.type_annotation = StrawberryAnnotation(
            field_type,
            namespace=vars(module) if module is not None else None,
        )
    elif strawberry_field.type_annotation.namespace is None:
        # set by `strawberry.field(graphql_type=...)`
        strawberry_field.type_annotation.set_namespace_from_field(strawberry_field)

    # pydantic applies defaults when it builds the model
    strawberry_field.default = dataclasses.MISSING
    strawberry_field.default_factory = dataclasses.MISSING
    strawberry_field.default_value = dataclasses.MISSING

    return strawberry_field


def _get_type_var_map(cls: type[BaseModel]) -> dict[str, StrawberryType | type]:
    """Map the type parameters of the generic pydantic models `cls` extends."""
    type_var_map: dict[str, StrawberryType | type] = {}

    for base in cls.__mro__:
        metadata = getattr(base, "__pydantic_generic_metadata__", None)

        if not metadata or metadata["origin"] is None:
            continue

        parameters = metadata["origin"].__pydantic_generic_metadata__["parameters"]

        for parameter, argument in zip(parameters, metadata["args"], strict=False):
            if isinstance(argument, type):
                argument = _CONSTRAINED_DATE_TYPES.get(argument, argument)  # noqa: PLW2901

            type_var_map.setdefault(
                parameter.__name__, StrawberryAnnotation(argument).resolve()
            )

    return type_var_map


def get_resolver_fields(
    cls: type[BaseModel], *, is_input: bool
) -> list[StrawberryField]:
    """Collect the fields with a resolver of `cls` and of its bases."""
    for field_name, field_info in cls.model_fields.items():
        default = field_info.default

        # pydantic uses a method that overrides a field as the field's default,
        # and removes it from the class. A field that overrides an inherited
        # method uses it as default too, but the method is still in its class
        if get_resolver_field(default) is not None and not any(
            vars(base).get(field_name) is default for base in cls.__mro__
        ):
            raise ResolverFieldOverridesModelFieldError(field_name=field_name, cls=cls)

    if is_input:
        # resolvers inherited from e.g. a base shared with an output type are
        # ignored, as input types only hold the values sent by the client
        for attribute, value in vars(cls).items():
            if (resolver_field := get_resolver_field(value)) is not None:
                raise ResolverFieldOnInputError(
                    field_name=attribute, cls=cls, resolver_field=resolver_field
                )

        return []

    resolver_fields: dict[str, StrawberryField] = {}

    # bases first, so that subclasses can override their fields
    for base in reversed(cls.__mro__):
        # e.g. a data field that overrides an inherited resolver field
        for name in get_annotations(base, format=Format.FORWARDREF):
            resolver_fields.pop(name, None)

        for attribute, value in list(vars(base).items()):
            if (resolver_field := get_resolver_field(value)) is not None:
                resolver_fields[attribute] = resolver_field
            else:
                resolver_fields.pop(attribute, None)

    type_var_map = _get_type_var_map(cls)
    fields = []

    for attribute, resolver_field in resolver_fields.items():
        field = copy.copy(resolver_field)
        # e.g. `label = strawberry.pydantic.field(get_label)` is named `label`
        field.python_name = attribute
        field.origin = cls

        resolver = field.base_resolver
        assert resolver is not None

        # like `@strawberry.type`, class methods are bound to the class
        if isinstance(wrapped_func := resolver.wrapped_func, classmethod):
            field = field(types.MethodType(wrapped_func.__func__, cls))

        if (
            field.type_annotation is not None
            and field.type_annotation.namespace is None
        ):
            # set by `graphql_type=...`, which is resolved like the resolver's
            # own annotations
            field.type_annotation.namespace = resolver._namespace

        if type_var_map and field.is_graphql_generic:
            field = field.copy_with(type_var_map)

        fields.append(field)

    return fields


def get_pydantic_fields(
    cls: type[BaseModel],
    is_input: bool = False,
    include_computed: bool = False,
) -> list[StrawberryField]:
    """Extract StrawberryFields from a Pydantic BaseModel class.

    Pydantic is the source of truth for which fields exist: its `model_fields`
    already resolved string annotations and merged inherited fields. Fields are
    excluded from the schema when they are marked with `strawberry.Private` or,
    for output types, with pydantic's `Field(exclude=True)`.

    Fields can be customized using `Annotated`, like with `@strawberry.type`:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[SomeDirective()])]

    Args:
        cls: The Pydantic BaseModel class to extract fields from
        is_input: Whether this is for an input type
        include_computed: Whether to include computed fields

    Returns:
        List of StrawberryField instances
    """
    fields: list[StrawberryField] = []

    field_names = list(cls.model_fields)

    if include_computed:
        field_names.extend(cls.model_computed_fields)

    origins = _get_field_origins(cls)

    for field_name in field_names:
        # computed fields don't have a FieldInfo
        field_info = cls.model_fields.get(field_name)

        if field_info is None:
            # computed fields are properties, not annotations
            origin = next(
                (base for base in cls.__mro__ if field_name in vars(base)), cls
            )
        else:
            origin = origins.get(field_name, cls)

        if field_info is None:
            # e.g. `-> strawberry.Private[int]` on a computed field
            if is_private(cls.model_computed_fields[field_name].return_type):
                continue
        else:
            if is_private(field_info.rebuild_annotation()):
                continue

            # `exclude=True` hides a field from pydantic's serialization, so we
            # hide it from the GraphQL output too
            if field_info.exclude is True and not is_input:
                continue

            # Uploads are the integration's file objects, which pydantic would
            # reject on every request when validating them as `Upload` (bytes)
            if is_input and _contains_upload(field_info.annotation):
                raise UploadFieldError(field_name=field_name, cls=origin)

            if is_input and _annotation_is_maybe(field_info.annotation):
                raise MaybeFieldError(field_name=field_name, cls=origin)

        if (base_field := _get_strawberry_base_field(origin, field_name)) is not None:
            # inputs replace the field's default with pydantic's below
            strawberry_field = copy.copy(base_field) if is_input else base_field
        else:
            strawberry_field = _create_strawberry_field(
                cls, origin, field_name, field_info, is_input=is_input
            )

        if is_input and field_info is not None:
            _set_input_default(strawberry_field, field_info)

        fields.append(strawberry_field)

    return fields


__all__ = ["get_pydantic_fields", "get_resolver_fields"]
