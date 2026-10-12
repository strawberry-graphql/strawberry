"""Read the fields of Pydantic models as Strawberry fields."""

from __future__ import annotations

import copy
import dataclasses
import functools
import sys
import types
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    TypeGuard,
    get_args,
    get_origin,
)
from typing_extensions import Format, get_annotations

from graphql.type.directives import DEFAULT_DEPRECATION_REASON
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    MultipleStrawberryFieldsError,
    ResolverFieldOnInputError,
)
from strawberry.file_uploads import Upload
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, get_annotated_field
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.types.private import is_private

from .exceptions import (
    MaybeFieldError,
    MisplacedFieldError,
    UnregisteredPydanticTypeError,
    UnsupportedFieldOverrideError,
    UnsupportedInheritedFieldError,
    UploadFieldError,
)
from .resolver_field import get_resolver_field, is_field_decorator

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic.fields import FieldInfo

    from strawberry.exceptions import StrawberryException
    from strawberry.types.base import StrawberryType


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


def _get_annotated_metadata(annotation: object) -> Iterator[object]:
    """Yield the metadata of the `Annotated` types in `annotation`, at any depth."""
    if get_origin(annotation) is Annotated:
        annotation, *metadata = get_args(annotation)

        yield from metadata
        yield from _get_annotated_metadata(annotation)
    else:
        for arg in get_args(annotation):
            yield from _get_annotated_metadata(arg)


def _get_strawberry_field_override(
    field_info: FieldInfo, cls: type, field_name: str
) -> StrawberryField | None:
    """Return the `strawberry.field()` from `Annotated[T, strawberry.field()]`.

    `cls` is the class that declares the field.
    """
    # Pydantic treats a `strawberry.field()` assigned as the default like a
    # dataclass field: it keeps its default and discards everything else. The
    # original object is only kept on a private attribute, so this check is best
    # effort.
    if isinstance(getattr(field_info, "_original_assignment", None), StrawberryField):
        raise MisplacedFieldError(field_name=field_name, cls=cls, usage="default")

    # `strawberry.pydantic.field` is only for fields with a resolver
    if is_field_decorator(field_info.default) or any(
        is_field_decorator(item)
        for item in (
            *field_info.metadata,
            *_get_annotated_metadata(field_info.annotation),
        )
    ):
        raise MisplacedFieldError(field_name=field_name, cls=cls, usage="model_field")

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


def _set_input_default(field: StrawberryField, field_info: FieldInfo) -> None:
    # Let Strawberry's schema converter handle explicit defaults, including
    # None and model instances, using the field's actual GraphQL type.
    default = (
        dataclasses.MISSING
        if field_info.default is PydanticUndefined
        else field_info.default
    )

    # `StrawberryField.__copy__` builds `default_value` from `default`
    field.default = default
    field.default_factory = dataclasses.MISSING
    field.default_value = default

    # Factories belong to Pydantic: they run for each input and may need the
    # other validated fields. Nullable GraphQL fields allow clients to omit them.
    if field_info.default_factory is not None:
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


def _get_computed_field_annotation(
    cls: type[BaseModel], origin: type, field_name: str
) -> tuple[Any, StrawberryField | None]:
    """Return the type of a computed field and its `strawberry.field()`, if any."""
    computed_field_info = cls.model_computed_fields[field_name]
    annotation = computed_field_info.return_type

    # `strawberry.pydantic.field` is only for fields with a resolver
    if any(is_field_decorator(item) for item in _get_annotated_metadata(annotation)):
        raise MisplacedFieldError(
            field_name=field_name, cls=origin, usage="model_field"
        )

    if get_origin(annotation) is not Annotated:
        return annotation, None

    annotation, *metadata = get_args(annotation)
    strawberry_fields = [item for item in metadata if isinstance(item, StrawberryField)]

    if len(strawberry_fields) > 1:
        raise MultipleStrawberryFieldsError(field_name=field_name, cls=origin)

    return (
        annotation,
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
        annotation = field_info.annotation
        description = field_info.description
        strawberry_override = _get_strawberry_field_override(
            field_info, origin, field_name
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
            annotation, namespace=namespace
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
    return UnregisteredPydanticTypeError(
        model, cls=cls, field_name=field_name, is_input=is_input
    )


def _get_type_var_map(
    cls: type[BaseModel],
) -> tuple[dict[str, StrawberryType | type], dict[str, type[BaseModel]]]:
    """Map the type parameters of the generic pydantic models `cls` extends.

    The arguments are converted like the types of data fields, so fields with a
    resolver typed with a type parameter get the same GraphQL type. Arguments
    that are models without a GraphQL definition are returned apart, by type
    parameter name, so that only the fields using them raise an error.
    """
    type_var_map: dict[str, StrawberryType | type] = {}
    unregistered_models: dict[str, type[BaseModel]] = {}

    for base in cls.__mro__:
        metadata = getattr(base, "__pydantic_generic_metadata__", None)

        if not metadata or metadata["origin"] is None:
            continue

        parameters = metadata["origin"].__pydantic_generic_metadata__["parameters"]

        for parameter, argument in zip(parameters, metadata["args"], strict=False):
            if parameter.__name__ in type_var_map:
                continue

            if (unregistered := _find_unregistered_model(argument, cls)) is not None:
                unregistered_models[parameter.__name__] = unregistered

            type_var_map[parameter.__name__] = StrawberryAnnotation(argument).resolve()

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
            raise UnsupportedFieldOverrideError(
                field_name=field_name, cls=cls, overridden="model_field"
            )

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
    # resolver fields overridden by an attribute that isn't a field, like a
    # method without `strawberry.pydantic.field`, and the base defining it
    overridden_by: dict[str, type] = {}

    # bases first, so that subclasses can override their fields
    for base in reversed(cls.__mro__):
        # e.g. a data field that overrides an inherited resolver field
        for name in get_annotations(base, format=Format.FORWARDREF):
            resolver_fields.pop(name, None)
            overridden_by.pop(name, None)

        for attribute, value in list(vars(base).items()):
            # pydantic types only read `strawberry.field()` from Strawberry types,
            # but a model that makes pydantic ignore `StrawberryField`, or a class
            # that isn't decorated, can still have one
            if _is_strawberry_resolver_field(value):
                raise MisplacedFieldError(
                    field_name=attribute, cls=base, usage="resolver", field=value
                )

            if (resolver_field := get_resolver_field(value)) is not None:
                resolver_fields[attribute] = resolver_field
                overridden_by.pop(attribute, None)
            elif include_computed and _is_computed_field(base, attribute, value):
                # computed fields replace resolver fields, like data fields
                resolver_fields.pop(attribute, None)
                overridden_by.pop(attribute, None)
            elif attribute in resolver_fields:
                del resolver_fields[attribute]
                overridden_by[attribute] = base

    # checked once the bases have been walked, as a subclass can define the
    # field again
    if overridden_by:
        attribute, base = next(iter(overridden_by.items()))

        raise UnsupportedFieldOverrideError(
            field_name=attribute, cls=base, overridden="resolver_field"
        )

    type_var_map, unregistered_models = _get_type_var_map(cls)
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
            for type_var in field.type_params:
                if (model := unregistered_models.get(type_var.__name__)) is not None:
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
            # dataclasses don't keep a default factory on the class, so pydantic
            # doesn't see it and requires the field, which clients can omit when
            # it's nullable
            if (
                is_input
                and field_info is not None
                and field_info.is_required()
                and base_field.default_factory is not dataclasses.MISSING
            ):
                raise UnsupportedInheritedFieldError(
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
