"""Read the fields of Pydantic models as Strawberry fields."""

from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import functools
import ipaddress
import math
import sys
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
    TypeGuard,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from typing_extensions import Format, get_annotations

import pydantic
import pydantic.networks
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
    ResolverFieldOnInputError,
)
from strawberry.file_uploads import Upload
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, get_annotated_field
from strawberry.types.lazy_type import StrawberryLazyReference
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.types.private import StrawberryPrivate, is_private
from strawberry.types.union import StrawberryUnion
from strawberry.types.unresolved_annotations import find_unresolved_options
from strawberry.utils.inspect import get_generic_arguments
from strawberry.utils.typing import is_union

from .exceptions import (
    AttributeOverridesComputedFieldError,
    AttributeOverridesResolverFieldError,
    InheritedDefaultFactoryError,
    InheritedStrawberryResolverError,
    MaybeFieldError,
    PydanticFieldWithoutResolverError,
    ResolverFieldOverridesModelFieldError,
    StrawberryFieldAsDefaultError,
    StrawberryFieldInModelError,
    UnregisteredPydanticTypeError,
    UnresolvedAnnotatedFieldError,
    UnsupportedRootModelError,
    UploadFieldError,
)
from .resolver_field import get_resolver_field, is_field_decorator

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator, Mapping

    from pydantic.fields import FieldInfo

    from strawberry.exceptions import StrawberryException
    from strawberry.types.base import StrawberryType


def _is_new_type(annotation: object) -> bool:
    return callable(annotation) and hasattr(annotation, "__supertype__")


def _is_subclass(annotation: object, base: type | tuple[type, ...]) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, base)


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

    return definition.get_field(field_name)


def _is_strawberry_resolver_field(value: object) -> TypeGuard[StrawberryField]:
    """Whether `value` is a `strawberry.field()` with a resolver."""
    return isinstance(value, StrawberryField) and value.base_resolver is not None


def _get_strawberry_base_resolver_fields(base: type) -> list[StrawberryField] | None:
    """Return the fields with a resolver of a regular Strawberry type or interface.

    Returns `None` for other classes. Strawberry keeps the resolvers of its types
    on the class as plain functions, so only the type's definition knows that
    they're fields.
    """
    if issubclass(base, BaseModel):
        return None

    # only the class's own definition, not one inherited from its bases
    definition = vars(base).get("__strawberry_definition__")

    if not isinstance(definition, StrawberryObjectDefinition):
        return None

    return [field for field in definition.fields if field.base_resolver is not None]


def _get_annotated_metadata(annotation: object) -> Iterator[object]:
    """Yield the metadata of the `Annotated` types in `annotation`, at any depth."""
    if get_origin(annotation) is Annotated:
        annotation, *metadata = get_args(annotation)

        yield from metadata
        yield from _get_annotated_metadata(annotation)
    else:
        for arg in get_args(annotation):
            yield from _get_annotated_metadata(arg)


# Strawberry reads these from the type when it resolves it, while other metadata,
# like `strawberry.field()` or Pydantic's `Field()`, configures the field
_TYPE_METADATA = (StrawberryLazyReference, StrawberryPrivate, StrawberryUnion)


def _is_option(value: object) -> bool:
    return not isinstance(value, _TYPE_METADATA)


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

    module = sys.modules.get(cls.__module__)
    namespace = vars(module) if module is not None else {}

    if (
        find_unresolved_options(
            annotation, namespace, cls=cls, field_name=field_name, is_option=_is_option
        )
        is not None
    ):
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

    # pydantic keeps the metadata of the field's `Annotated` apart from its type
    annotation = (
        Annotated[(field_info.annotation, *field_info.metadata)]
        if field_info.metadata
        else field_info.annotation
    )
    _, strawberry_field = get_annotated_field(
        annotation, cls=cls, field_name=field_name
    )

    return strawberry_field


def _contains_upload(annotation: object) -> bool:
    return annotation is Upload or any(
        _contains_upload(arg) for arg in get_args(annotation)
    )


# pydantic types that only add validation to a date or datetime
_CONSTRAINED_DATE_TYPES: dict[type, type] = {
    AwareDatetime: dt.datetime,
    NaiveDatetime: dt.datetime,
    PastDatetime: dt.datetime,
    FutureDatetime: dt.datetime,
    PastDate: dt.date,
    FutureDate: dt.date,
}

# pydantic types exposed with the GraphQL type of their python equivalent. The
# values of the ones exposed as strings are serialized with `str()`, and
# validated from strings by pydantic
# (type checkers see the `IPvAny*` types as unions of `ipaddress` types)
_PYDANTIC_TYPES: dict[object, type] = {
    pydantic.EmailStr: str,
    pydantic.NameEmail: str,
    pydantic.IPvAnyAddress: str,
    pydantic.IPvAnyInterface: str,
    pydantic.IPvAnyNetwork: str,
    pydantic.SecretStr: str,
}

# pydantic's URL types, like `HttpUrl` or `MongoDsn`, and the ones defined by
# users, are exposed as strings. Multi-host URLs, like `PostgresDsn`, don't
# extend `AnyUrl`, and their base class is private
_URL_TYPES: tuple[type, ...] = (
    pydantic.AnyUrl,
    pydantic_core.Url,
    pydantic_core.MultiHostUrl,
    *(
        (base,)
        if (base := getattr(pydantic.networks, "_BaseMultiHostUrl", None))
        else ()
    ),
)


# What pydantic validates the types exposed as strings to, so the defaults that
# can be published for them. `SecretStr` defaults aren't published, as they'd be
# part of the schema
_PYDANTIC_VALUE_TYPES: dict[object, tuple[type, ...]] = {
    pydantic.EmailStr: (str,),
    pydantic.NameEmail: (pydantic.NameEmail,),
    pydantic.IPvAnyAddress: (ipaddress.IPv4Address, ipaddress.IPv6Address),
    pydantic.IPvAnyInterface: (ipaddress.IPv4Interface, ipaddress.IPv6Interface),
    pydantic.IPvAnyNetwork: (ipaddress.IPv4Network, ipaddress.IPv6Network),
}


def _get_pydantic_type_equivalent(type_: type) -> type:
    """Return the type Strawberry exposes a pydantic type as, or `type_`."""
    if type_ in _PYDANTIC_TYPES:
        return _PYDANTIC_TYPES[type_]

    if _is_subclass(type_, _URL_TYPES):
        return str

    return type_


# GraphQL's Int is a 32-bit integer
_GRAPHQL_INT_RANGE = range(-(2**31), 2**31)
_CONSTANT_TYPES = (
    str,
    bool,
    Decimal,
    dt.date,
    dt.datetime,
    dt.time,
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

    if isinstance(annotation, type) and annotation in _PYDANTIC_VALUE_TYPES:
        return type(value) in _PYDANTIC_VALUE_TYPES[annotation]

    # e.g. an `HttpUrl` default, but not a string that pydantic would convert
    if _is_subclass(annotation, _URL_TYPES):
        return type(value) is annotation

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


def _find_unregistered_model(
    type_: Any, model: type[BaseModel]
) -> type[BaseModel] | None:
    """Return a model used in `type_` that doesn't have a GraphQL type, if any."""
    if _is_subclass(type_, BaseModel):
        # `model` can reference itself, but it's only registered after its
        # fields. The definition is inherited by subclasses, which would
        # otherwise be the GraphQL type of their decorated base, and by
        # parametrized generic models, like `Page[User]`
        if type_ is model or "__strawberry_definition__" in vars(type_):
            return None

        return type_

    return next(
        (
            unregistered
            for arg in get_args(type_)
            if (unregistered := _find_unregistered_model(arg, model)) is not None
        ),
        None,
    )


def _replace_pydantic_types(type_: Any) -> Any:
    """Replace the pydantic types in `type_` with the types used by Strawberry.

    NewTypes are kept: they're resolved by the schema's scalar registry, like with
    `@strawberry.type`. That's how `strawberry.ID`, `JSON`, `Upload` and
    `scalar_map` scalars work.
    """
    if isinstance(type_, type):
        type_ = _CONSTRAINED_DATE_TYPES.get(type_, type_)
        type_ = _get_pydantic_type_equivalent(type_)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return type_

    args = tuple(_replace_pydantic_types(arg) for arg in get_args(type_))

    if is_union(type_):
        # `X | Y` can't be subscripted, so the union is rebuilt with `Union`
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

    return get_annotated_field(annotation, cls=origin, field_name=field_name)


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

    # like `strawberry.field(deprecation_reason=...)`, deprecating a required
    # input field fails schema validation, as GraphQL doesn't allow it
    if (
        strawberry_field.deprecation_reason is None
        and deprecated_field_info is not None
        and deprecated_field_info.deprecated
    ):
        strawberry_field.deprecation_reason = (
            DEFAULT_DEPRECATION_REASON
            if deprecated_field_info.deprecated is True
            else deprecated_field_info.deprecation_message
        )

    # types are resolved in the module declaring the field
    module = sys.modules.get(origin.__module__)
    namespace = vars(module) if module is not None else None

    if strawberry_field.type_annotation is None:
        if (unregistered := _find_unregistered_model(annotation, cls)) is not None:
            raise _unregistered_model_error(
                unregistered, cls=origin, field_name=field_name, is_input=is_input
            )

        strawberry_field.type_annotation = StrawberryAnnotation(
            _replace_pydantic_types(annotation), namespace=namespace
        )
    else:
        # set by `strawberry.field(graphql_type=...)`, whose annotation can be
        # shared with other types, e.g. through a type alias, so each field gets
        # its own, instead of setting the namespace of the shared one
        strawberry_field.type_annotation = StrawberryAnnotation(
            strawberry_field.type_annotation.raw_annotation, namespace=namespace
        )

    # pydantic applies defaults when it builds the model
    strawberry_field.default = dataclasses.MISSING
    strawberry_field.default_factory = dataclasses.MISSING
    strawberry_field.default_value = dataclasses.MISSING

    return strawberry_field


def _unregistered_model_error(
    model: type[BaseModel], *, cls: type, field_name: str, is_input: bool
) -> StrawberryException:
    """The error for a field using a model without a GraphQL definition."""
    if issubclass(model, RootModel):
        return UnsupportedRootModelError(model, cls=cls, field_name=field_name)

    return UnregisteredPydanticTypeError(
        model, cls=cls, field_name=field_name, is_input=is_input
    )


def _split_pydantic_base(base: Any) -> tuple[Any, tuple[Any, ...]]:
    """Return the class and the arguments of a base of a pydantic model.

    Pydantic parametrizes generic models with subclasses, like `Page[int]`, and
    returns the model itself for `Page[T]` when `T` is its own type parameter,
    like in `class Wrapper(Page[T], Generic[T])`.
    """
    metadata = getattr(base, "__pydantic_generic_metadata__", None)

    if metadata is None:
        return get_origin(base) or base, get_args(base)

    if metadata["origin"] is None:
        return base, tuple(metadata["parameters"])

    return metadata["origin"], tuple(metadata["args"])


def _get_type_var_map(
    cls: type[BaseModel], arguments: Mapping[TypeVar, Any]
) -> tuple[dict[str, StrawberryType | type], dict[str, type[BaseModel]]]:
    """Map the type parameters of a generic model to the arguments `cls` gives them.

    The arguments are converted like the types of data fields, so fields with a
    resolver typed with a type parameter get the same GraphQL type. Arguments
    that are models without a GraphQL definition are returned apart, by type
    parameter name, so that only the fields using them raise an error.
    """
    type_var_map: dict[str, StrawberryType | type] = {}
    unregistered_models: dict[str, type[BaseModel]] = {}

    for parameter, argument in arguments.items():
        # e.g. the type parameter of a generic model that isn't parametrized
        if isinstance(argument, TypeVar):
            continue

        if (unregistered := _find_unregistered_model(argument, cls)) is not None:
            unregistered_models[parameter.__name__] = unregistered

        type_var_map[parameter.__name__] = StrawberryAnnotation(
            _replace_pydantic_types(argument)
        ).resolve()

    return type_var_map, unregistered_models


def _is_computed_field(base: type, attribute: str, value: object) -> bool:
    """Whether `value` is the computed field `attribute` defined by `base`.

    The computed fields of a model include the inherited ones, even when a
    subclass overrides them with something else, so the attribute is compared
    to the computed field itself.
    """
    decorators = vars(base).get("__pydantic_decorators__")

    if decorators is None or attribute not in decorators.computed_fields:
        return False

    if isinstance(value, property):
        getter = value.fget
    elif isinstance(value, functools.cached_property):
        getter = value.func
    else:
        return False

    return getter is decorators.computed_fields[attribute].func


def get_resolver_fields(
    cls: type[BaseModel], *, is_input: bool, include_computed: bool
) -> list[StrawberryField]:
    """Collect the fields with a resolver of `cls` and of its bases.

    Computed fields override inherited resolver fields only when they're
    included in the type, otherwise the field would be removed.
    """
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
            # e.g. a `@strawberry.field` method in a model that makes pydantic
            # ignore `StrawberryField`
            resolver_field = (
                value
                if _is_strawberry_resolver_field(value)
                else get_resolver_field(value)
            )

            if resolver_field is not None:
                raise ResolverFieldOnInputError(
                    field_name=attribute, cls=cls, resolver_field=resolver_field
                )

        return []

    resolver_fields: dict[str, StrawberryField] = {}
    # the model declaring each resolver, whose type parameters it uses
    declared_in: dict[str, type] = {}
    computed_fields: set[str] = set()
    # fields overridden by an attribute that isn't a field, like a method
    # without `strawberry.pydantic.field`, with the base defining it and the
    # error to raise
    overridden_by: dict[
        str,
        tuple[
            type,
            type[
                AttributeOverridesResolverFieldError
                | AttributeOverridesComputedFieldError
            ],
        ],
    ] = {}

    # bases first, so that subclasses can override their fields
    for base in reversed(cls.__mro__):
        # e.g. a data field that overrides an inherited resolver field
        for name in get_annotations(base, format=Format.FORWARDREF):
            resolver_fields.pop(name, None)
            computed_fields.discard(name)
            overridden_by.pop(name, None)

        # e.g. the `@strawberry.field` methods of a regular Strawberry interface
        if (base_fields := _get_strawberry_base_resolver_fields(base)) is not None:
            for base_field in base_fields:
                assert base_field.python_name is not None

                resolver_fields[base_field.python_name] = base_field
                declared_in[base_field.python_name] = base
                computed_fields.discard(base_field.python_name)
                overridden_by.pop(base_field.python_name, None)

            continue

        for attribute, value in list(vars(base).items()):
            # pydantic types only read `strawberry.field()` from Strawberry types,
            # but a model that makes pydantic ignore `StrawberryField`, or a class
            # that isn't decorated, can still have one
            if _is_strawberry_resolver_field(value):
                raise StrawberryFieldInModelError(
                    field_name=attribute, cls=base, field=value
                )

            if (resolver_field := get_resolver_field(value)) is not None:
                resolver_fields[attribute] = resolver_field
                declared_in[attribute] = base
                computed_fields.discard(attribute)
                overridden_by.pop(attribute, None)
            elif include_computed and _is_computed_field(base, attribute, value):
                # computed fields replace resolver fields, like data fields
                resolver_fields.pop(attribute, None)
                computed_fields.add(attribute)
                overridden_by.pop(attribute, None)
            elif attribute in resolver_fields:
                del resolver_fields[attribute]
                overridden_by[attribute] = (base, AttributeOverridesResolverFieldError)
            # a property only changes the value of a computed field, but pydantic
            # would use e.g. a method itself as the value
            elif attribute in computed_fields and not isinstance(
                value, (property, functools.cached_property)
            ):
                computed_fields.discard(attribute)
                overridden_by[attribute] = (base, AttributeOverridesComputedFieldError)

    # checked once the bases have been walked, as a subclass can define the
    # field again
    if overridden_by:
        attribute, (base, error) = next(iter(overridden_by.items()))

        raise error(field_name=attribute, cls=base)

    generic_arguments = get_generic_arguments(cls, _split_pydantic_base)
    fields = []

    for attribute, resolver_field in resolver_fields.items():
        # e.g. `label = strawberry.pydantic.field(get_label)` is named `label`.
        # It's set before copying, as copying reads the name, which falls back
        # to the resolver's `__name__`, and `functools.partial` doesn't have one
        resolver_field.python_name = attribute
        field = copy.copy(resolver_field)
        field.origin = cls

        resolver = field.base_resolver
        assert resolver is not None

        # like `@strawberry.type`, static and class methods are bound to the
        # class, also when they're inherited from a regular Strawberry type
        field.base_resolver = resolver = resolver.bind(cls)

        if (
            field.type_annotation is not None
            and field.type_annotation.namespace is None
        ):
            # set by `graphql_type=...`, which is resolved like the resolver's
            # own annotations
            field.type_annotation.namespace = resolver._namespace

        if field.is_graphql_generic:
            type_var_map, unregistered_models = _get_type_var_map(
                cls, generic_arguments.get(declared_in[attribute], {})
            )
            type_params = [type_var.__name__ for type_var in field.type_params]

            # e.g. a resolver of a generic model that isn't parametrized
            if all(name in type_var_map for name in type_params):
                for name in type_params:
                    if (model := unregistered_models.get(name)) is not None:
                        raise _unregistered_model_error(
                            model, cls=cls, field_name=attribute, is_input=False
                        )

                field = field.copy_with(type_var_map)

        fields.append(field)

    return fields


def get_pydantic_fields(
    cls: type[BaseModel],
    is_input: bool = False,
    include_computed: bool = False,
    resolver_field_names: Collection[str] = (),
) -> list[StrawberryField]:
    """Return the Strawberry fields of a Pydantic model.

    Pydantic is the source of truth for which fields exist: its `model_fields`
    already resolved string annotations and merged inherited fields. Fields are
    excluded from the schema when they are marked with `strawberry.Private` or,
    for output types, with pydantic's `Field(exclude=True)`.

    Fields can be customized using `Annotated`, like with `@strawberry.type`:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[SomeDirective()])]

    `resolver_field_names` are the names of the resolver fields of `cls`, which
    replace the computed fields with the same name.
    """
    fields: list[StrawberryField] = []

    field_names = list(cls.model_fields)

    if include_computed:
        # replaced computed fields are left out before their type is resolved,
        # as it doesn't have to be a Strawberry type
        field_names.extend(
            name
            for name in cls.model_computed_fields
            if name not in resolver_field_names
        )

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
            # pydantic sees the annotation of a field with a resolver, like
            # `label: str = strawberry.field(resolver=get_label)`, and makes it a
            # field of the model, with the resolver as its default value
            if base_field.base_resolver is not None:
                raise InheritedStrawberryResolverError(
                    field_name=field_name, cls=cls, base=origin
                )

            # dataclasses don't keep a default factory on the class, so pydantic
            # doesn't see it and requires the field, which clients can omit when
            # it's nullable
            if (
                is_input
                and field_info is not None
                and field_info.is_required()
                and base_field.default_factory is not dataclasses.MISSING
            ):
                raise InheritedDefaultFactoryError(
                    field_name=field_name, cls=cls, base=origin
                )

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
