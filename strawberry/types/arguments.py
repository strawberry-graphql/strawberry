from __future__ import annotations

import dataclasses
import inspect
import types
from dataclasses import MISSING
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ForwardRef,
    Union,
    cast,
    get_args,
    get_origin,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import MultipleStrawberryArgumentsError, UnsupportedTypeError
from strawberry.scalars import is_scalar
from strawberry.types.base import (
    StrawberryList,
    StrawberryMaybe,
    StrawberryOptional,
    StrawberryType,
    get_object_definition,
    has_object_definition,
)
from strawberry.types.enum import StrawberryEnumDefinition, has_enum_definition
from strawberry.types.lazy_type import LazyType, StrawberryLazyReference
from strawberry.types.maybe import Some
from strawberry.types.unset import UNSET

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from strawberry.relay.types import GlobalID
    from strawberry.schema.config import StrawberryConfig
    from strawberry.types.info import Info
    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper


class StrawberryArgumentAnnotation:
    description: str | None
    name: str | None
    deprecation_reason: str | None
    directives: Iterable[object]
    metadata: Mapping[Any, Any]
    graphql_type: Any | None

    def __init__(  # noqa: PLR0917
        self,
        description: str | None = None,
        name: str | None = None,
        deprecation_reason: str | None = None,
        directives: Iterable[object] = (),
        metadata: Mapping[Any, Any] | None = None,
        graphql_type: Any | None = None,
    ) -> None:
        self.description = description
        self.name = name
        self.deprecation_reason = deprecation_reason
        self.directives = directives
        self.metadata = metadata or {}
        self.graphql_type = graphql_type


class StrawberryArgument:
    def __init__(  # noqa: PLR0917
        self,
        python_name: str,
        graphql_name: str | None,
        type_annotation: StrawberryAnnotation,
        is_subscription: bool = False,
        description: str | None = None,
        default: object = UNSET,
        deprecation_reason: str | None = None,
        directives: Iterable[object] = (),
        metadata: Mapping[Any, Any] | None = None,
    ) -> None:
        self.python_name = python_name
        self.graphql_name = graphql_name
        self.is_subscription = is_subscription
        self.description = description
        self.type_annotation = type_annotation
        self.deprecation_reason = deprecation_reason
        self.directives = tuple(directives)
        self.metadata = metadata or {}

        self.global_id_expected_types: tuple[type | LazyType, ...] = ()

        # TODO: Consider moving this logic to a function
        self.default = UNSET if default is inspect.Parameter.empty else default

        annotation = type_annotation.annotation
        if not isinstance(annotation, str):
            resolved_annotation = annotation
            _check_nested_global_id_expected_types(resolved_annotation)
            if get_origin(resolved_annotation) is Annotated:
                first, *rest = get_args(resolved_annotation)

                # Only `strawberry.argument()` is removed, as the rest of the
                # metadata, like `strawberry.enum(name=...)`, is part of the type
                type_metadata = [
                    arg
                    for arg in rest
                    if not isinstance(arg, StrawberryArgumentAnnotation)
                ]
                self.type_annotation = StrawberryAnnotation(
                    Annotated[(first, *type_metadata)] if type_metadata else first,
                    namespace=type_annotation.namespace,
                )

                # Find any instances of StrawberryArgumentAnnotation
                # in the other Annotated args, raising an exception if there
                # are multiple StrawberryArgumentAnnotations
                argument_annotation_seen = False

                for arg in rest:
                    if isinstance(arg, StrawberryArgumentAnnotation):
                        if argument_annotation_seen:
                            raise MultipleStrawberryArgumentsError(
                                argument_name=python_name
                            )

                        argument_annotation_seen = True

                        self.description = arg.description
                        self.graphql_name = arg.name
                        self.deprecation_reason = arg.deprecation_reason
                        self.directives = tuple(arg.directives)
                        self.metadata = arg.metadata
                        if arg.graphql_type is not None:
                            self.type_annotation = StrawberryAnnotation(
                                arg.graphql_type
                            )

                    if isinstance(arg, StrawberryLazyReference):
                        if _is_global_id_annotation(first):
                            raise TypeError(
                                "A lazy reference used as an expected GlobalID "
                                "type must include the type name: "
                                'Annotated[GlobalID, Annotated["SomeType", '
                                'strawberry.lazy("...")]].'
                            )
                        self.type_annotation = StrawberryAnnotation(
                            arg.resolve_forward_ref(first)
                        )

                self.global_id_expected_types = _get_global_id_expected_types(
                    first, rest
                )
            elif get_origin(resolved_annotation) in (Union, types.UnionType):
                # Optional[Annotated[GlobalID, SomeType]]: the Annotated metadata
                # is nested inside the union, extract it from there
                annotated_args = [
                    arg
                    for arg in get_args(resolved_annotation)
                    if get_origin(arg) is Annotated
                ]
                if len(annotated_args) == 1:
                    first, *rest = get_args(annotated_args[0])
                    self.global_id_expected_types = _get_global_id_expected_types(
                        first, rest
                    )

    @property
    def type(self) -> StrawberryType | type:
        return self.type_annotation.resolve()

    @property
    def is_graphql_generic(self) -> bool:
        from strawberry.schema.compat import is_graphql_generic

        return is_graphql_generic(self.type)

    @property
    def is_maybe(self) -> bool:
        return isinstance(self.type, StrawberryMaybe)


def _is_leaf_type(
    type_: StrawberryType | type,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    skip_classes: tuple[type, ...] = (),
) -> bool:
    if type_ in skip_classes:
        return False

    if is_scalar(type_, scalar_registry):
        return True

    if isinstance(type_, StrawberryEnumDefinition):
        return True

    if isinstance(type_, LazyType):
        return _is_leaf_type(type_.resolve_type(), scalar_registry)

    return False


def _is_optional_leaf_type(
    type_: StrawberryType | type,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    skip_classes: tuple[type, ...] = (),
) -> bool:
    if type_ in skip_classes:
        return False

    if isinstance(type_, StrawberryOptional):
        return _is_leaf_type(type_.of_type, scalar_registry, skip_classes)

    return False


@dataclasses.dataclass(frozen=True)
class InputContext:
    """Passed to `StrawberryObjectDefinition.from_input` when building an input."""

    info: Info | None
    config: StrawberryConfig
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition]
    path: tuple[str | int, ...]
    """Location of the input value in the arguments, see `convert_argument`."""

    def convert(
        self, value: object, type_: StrawberryType | type, *keys: str | int
    ) -> object:
        """Convert a GraphQL input value of `type_` like Strawberry does.

        `keys` are the location of `value` in this input, as GraphQL field names
        and list indices, so that inputs nested in it know their location:

        ```python
        context.convert(value["items"][0], Item, "items", 0)
        ```

        `type_` can be a Strawberry type, like `field.resolve_type()`, or a Python
        annotation, like `list[Item]`.
        """
        if not isinstance(type_, StrawberryType) and get_origin(type_) is not None:
            type_ = cast("StrawberryType", StrawberryAnnotation(type_).resolve())

        return convert_argument(
            value,
            type_,
            self.scalar_registry,
            self.config,
            self.info,
            path=(*self.path, *keys),
        )


def convert_argument(
    value: object,
    type_: StrawberryType | type,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    config: StrawberryConfig,
    info: Info | None = None,
    *,
    path: tuple[str | int, ...] = (),
) -> object:
    """Convert a GraphQL input value of `type_` to its Python value.

    `path` is the location of the value in the arguments, made of GraphQL field
    names and list indices. It's passed on to input types that build their own
    value, see `StrawberryObjectDefinition.from_input`.
    """
    from strawberry.relay.types import (
        GlobalID,
        GlobalIDValueError,
        InvalidGlobalIDError,
    )

    # TODO: move this somewhere else and make it first class
    # Handle StrawberryMaybe first, since it extends StrawberryOptional
    if isinstance(type_, StrawberryMaybe):
        # Check if this is Maybe[T | None] (has StrawberryOptional as of_type)
        if isinstance(type_.of_type, StrawberryOptional):
            # This is Maybe[T | None] - allows null values
            res = convert_argument(
                value, type_.of_type, scalar_registry, config, info, path=path
            )

            return Some(res)

        if value is None:
            from strawberry.exceptions import StrawberryInputCoercionError

            type_name = getattr(type_.of_type, "__name__", str(type_.of_type))
            raise StrawberryInputCoercionError(
                f"Expected value of type '{type_name}', found null. "
                f"Field of type 'Maybe[{type_name}]' cannot be explicitly set to null. "
                f"Use 'Maybe[{type_name} | None]' if you need to allow null values."
            )

        # This is Maybe[T] - validation for null values is handled by MaybeNullValidationRule
        # Convert the value and wrap in Some()
        res = convert_argument(
            value, type_.of_type, scalar_registry, config, info, path=path
        )

        return Some(res)

    # Handle regular StrawberryOptional (not Maybe)
    if isinstance(type_, StrawberryOptional):
        return convert_argument(
            value, type_.of_type, scalar_registry, config, info, path=path
        )

    if value is None:
        return None

    if value is UNSET:
        return UNSET

    if isinstance(type_, StrawberryList):
        value_list = cast("Iterable", value)

        if _is_leaf_type(
            type_.of_type, scalar_registry, skip_classes=(GlobalID,)
        ) or _is_optional_leaf_type(
            type_.of_type, scalar_registry, skip_classes=(GlobalID,)
        ):
            # the items don't need converting, but the list is still copied:
            # graphql-core gives the same default to every request that omits
            # the value, so changes to it would leak into the next requests
            return list(value_list)

        return [
            convert_argument(
                x, type_.of_type, scalar_registry, config, info, path=(*path, index)
            )
            for index, x in enumerate(value_list)
        ]

    if _is_leaf_type(type_, scalar_registry):
        if type_ is GlobalID:
            try:
                return GlobalID.from_id(value)  # type: ignore
            except GlobalIDValueError as error:
                # like the built-in scalars, instead of the decoding error
                raise InvalidGlobalIDError(
                    f'Value cannot represent a GlobalID: "{value}".'
                ) from error

        return value

    if isinstance(type_, LazyType):
        return convert_argument(
            value, type_.resolve_type(), scalar_registry, config, info, path=path
        )

    if has_enum_definition(type_):
        enum_definition: StrawberryEnumDefinition = type_.__strawberry_definition__
        return convert_argument(
            value, enum_definition, scalar_registry, config, info, path=path
        )

    if has_object_definition(type_):
        type_definition = type_.__strawberry_definition__
        type_ = cast("type", type_)

        if type_definition.from_input is not None:
            return type_definition.from_input(
                type_,
                cast("Mapping", value),
                InputContext(
                    info=info,
                    config=config,
                    scalar_registry=scalar_registry,
                    path=path,
                ),
            )

        kwargs: dict[str, object | None] = {}
        if type_definition.is_input:
            # Set an implicit default of None for all input fields so that we can construct
            # input types with nullable fields that don't specify explicit default values.
            # graphql-core should already have validated that all non-nullable (required)
            # input fields are present in value, so those None values will be overwritten
            # by the loop below.
            kwargs = {
                field.python_name: None
                for field in type_definition.fields
                if field.default_value is MISSING and field.default_factory is MISSING
            }

        for field in type_definition.fields:
            value = cast("Mapping", value)
            graphql_name = config.name_converter.from_field(field)

            if graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[graphql_name],
                    field.resolve_type(type_definition=type_definition),
                    scalar_registry,
                    config,
                    info,
                    path=(*path, graphql_name),
                )

        return type_(**kwargs)

    raise UnsupportedTypeError(type_)


def _is_global_id_annotation(annotation: object) -> bool:
    from strawberry.relay.types import GlobalID

    if annotation is GlobalID:
        return True
    if get_origin(annotation) in (Union, types.UnionType):
        return any(arg is GlobalID for arg in get_args(annotation))
    return False


def _is_global_id_type_metadata(arg: object) -> bool:
    """Whether an Annotated metadata item looks like an expected GlobalID type."""
    if isinstance(arg, (LazyType, StrawberryLazyReference)):
        return True
    if isinstance(arg, type):
        return True
    if has_object_definition(arg):
        return True
    origin = get_origin(arg)
    if origin in (Union, types.UnionType):
        return True
    return origin is Annotated and any(
        isinstance(a, StrawberryLazyReference) for a in get_args(arg)
    )


def _contains_global_id(annotation: object) -> bool:
    """Whether the annotation tree contains GlobalID anywhere."""
    from strawberry.relay.types import GlobalID

    if annotation is GlobalID:
        return True
    return any(_contains_global_id(arg) for arg in get_args(annotation))


def _check_nested_global_id_expected_types(
    annotation: object, *, _allowed: bool = True
) -> None:
    """Reject GlobalID expected-type metadata in unsupported nested shapes.

    Expected types are only supported directly on the argument annotation
    (``Annotated[GlobalID, SomeType]``) or inside a single-member union with
    ``None`` (``Optional[Annotated[GlobalID, SomeType]]``). Anywhere else -
    inside lists, tuples, deeper unions, or other containers - the metadata
    would be silently ignored, so a clear error is raised instead. Metadata
    that does not look like a type expectation (plain strings, arbitrary
    objects) is ignored everywhere, as before this feature existed.
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        first, *rest = get_args(annotation)
        if _is_global_id_annotation(first):
            if not _allowed and any(_is_global_id_type_metadata(item) for item in rest):
                raise TypeError(
                    "Expected GlobalID types are only supported directly on "
                    "an argument annotation (e.g. Annotated[GlobalID, "
                    "SomeType]) or inside Optional[...], not nested inside "
                    f"{annotation!r}."
                )
            return
        if any(_is_global_id_type_metadata(item) for item in rest) and (
            _contains_global_id(first)
        ):
            raise TypeError(
                "Expected GlobalID types are only supported when the "
                "annotated type is GlobalID itself (or Optional of it), not "
                f"on {annotation!r}."
            )
        _check_nested_global_id_expected_types(first, _allowed=False)
        return
    if origin in (Union, types.UnionType):
        members = get_args(annotation)
        annotated_members = [m for m in members if get_origin(m) is Annotated]
        for member in members:
            if member is type(None):
                continue
            _check_nested_global_id_expected_types(
                member, _allowed=_allowed and len(annotated_members) == 1
            )
        return
    for arg in get_args(annotation):
        _check_nested_global_id_expected_types(arg, _allowed=False)


def _get_global_id_expected_types(
    first: object, rest: list[object]
) -> tuple[type | LazyType, ...]:
    """Extract expected type names for a GlobalID from Annotated metadata.

    Supports ``Annotated[GlobalID, SomeType]``, multiple types for a union of
    allowed types (``Annotated[GlobalID, TypeA, TypeB]`` or
    ``Annotated[GlobalID, TypeA | TypeB]``), and lazy references
    (``Annotated[GlobalID, Annotated["SomeType", strawberry.lazy("...")]]``).
    Returns an empty tuple when the underlying type is not a GlobalID.
    """
    if not _is_global_id_annotation(first):
        return ()

    expected: list[type | LazyType] = []

    def _collect(arg: object) -> None:
        if isinstance(arg, StrawberryArgumentAnnotation):
            # handled by the StrawberryArgument itself
            return
        if isinstance(arg, StrawberryLazyReference):
            raise TypeError(
                "A lazy reference used as an expected GlobalID type must "
                "include the type name: Annotated[GlobalID, "
                'Annotated["SomeType", strawberry.lazy("...")]].'
            )
        if get_origin(arg) is not None and has_object_definition(get_origin(arg)):
            raise TypeError(
                "Generic aliases are not supported as expected GlobalID "
                f"types, found {arg!r}; use the concrete strawberry type "
                "instead."
            )
        definition = get_object_definition(arg)
        if definition is not None:
            if definition.is_interface or definition.is_input:
                raise TypeError(
                    f"Expected GlobalID type {definition.name!r} is "
                    f"{'an interface' if definition.is_interface else 'an input type'}; "
                    "list the concrete object types instead."
                )
            expected.append(cast("type", arg))
        elif isinstance(arg, LazyType):
            expected.append(arg)
        elif get_origin(arg) in (Union, types.UnionType):
            for member in get_args(arg):
                _collect(member)
        elif get_origin(arg) is Annotated:
            sub_args = get_args(arg)
            lazy_reference = next(
                (a for a in sub_args if isinstance(a, StrawberryLazyReference)),
                None,
            )
            if lazy_reference is not None:
                forward_ref = sub_args[0]
                if not isinstance(forward_ref, ForwardRef):
                    forward_ref = ForwardRef(str(forward_ref))
                expected.append(lazy_reference.resolve_forward_ref(forward_ref))
            else:
                _collect(sub_args[0])
        elif isinstance(arg, type):
            raise TypeError(
                "Expected GlobalID types in Annotated metadata must be "
                f"strawberry types or lazy references, found {arg!r}."
            )
        # Anything else (plain strings, arbitrary objects, TypeVars, ...) is
        # ordinary Annotated metadata, not an expected-type declaration, so
        # it is ignored - as Strawberry treated it before expected-type
        # validation existed.

    for arg in rest:
        _collect(arg)
    return tuple(expected)


def _validate_global_id_type(
    value: GlobalID,
    expected_types: tuple[type | LazyType, ...],
    config: StrawberryConfig,
) -> None:
    """Validate a parsed GlobalID against the expected types from Annotated."""
    from strawberry.relay.types import InvalidGlobalIDError

    expected_names = []
    for expected_type in expected_types:
        if isinstance(expected_type, LazyType):
            try:
                resolved = expected_type.resolve_type()
            except (ImportError, AttributeError, KeyError) as error:
                raise TypeError(
                    "Could not resolve lazy GlobalID expected type "
                    f"{expected_type!r}: {error}"
                ) from error
        else:
            resolved = expected_type
        definition = get_object_definition(resolved)
        if definition is None:
            raise TypeError(
                f"Expected GlobalID type {expected_type!r} did not resolve to "
                "a strawberry type."
            )
        expected_names.append(config.name_converter.from_type(definition))

    expected_names = list(dict.fromkeys(expected_names))

    if value.type_name not in expected_names:
        expected = " or ".join(f'"{name}"' for name in expected_names)
        raise InvalidGlobalIDError(
            f'GlobalID type "{value.type_name}" does not match expected type {expected}.'
        )


def convert_arguments(
    value: dict[str, Any],
    arguments: list[StrawberryArgument],
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    config: StrawberryConfig,
    info: Info | None = None,
) -> dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values.

    `info` is passed on to input types that build their own value, see
    `StrawberryObjectDefinition.from_input`.
    """
    from strawberry.relay.types import GlobalID

    if not arguments:
        return {}

    kwargs = {}

    for argument in arguments:
        assert argument.python_name

        name = config.name_converter.from_argument(argument)

        if name in value:
            current_value = value[name]

            converted = convert_argument(
                value=current_value,
                type_=argument.type,
                config=config,
                scalar_registry=scalar_registry,
                info=info,
                path=(name,),
            )
            if argument.global_id_expected_types and isinstance(converted, GlobalID):
                _validate_global_id_type(
                    converted, argument.global_id_expected_types, config
                )
            kwargs[argument.python_name] = converted

    return kwargs


def argument(  # noqa: PLR0917
    description: str | None = None,
    name: str | None = None,
    deprecation_reason: str | None = None,
    directives: Iterable[object] = (),
    metadata: Mapping[Any, Any] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryArgumentAnnotation:
    """Function to add metadata to an argument, like a description or deprecation reason.

    Args:
        description: The GraphQL description of the argument
        name: The GraphQL name of the argument
        deprecation_reason: The reason why this argument is deprecated,
            setting this will mark the argument as deprecated
        directives: The directives to attach to the argument
        metadata: Metadata to attach to the argument, this can be used
            to store custom data that can be used by custom logic or plugins
        graphql_type: The GraphQL type for the argument, useful when you want to use a
            different type than the one in the schema.

    Returns:
        A StrawberryArgumentAnnotation object that can be used to customise an argument

    Example:
    ```python
    from typing import Annotated
    import strawberry


    @strawberry.type
    class Query:
        @strawberry.field
        def example(
            self,
            info: strawberry.Info,
            value: Annotated[int, strawberry.argument(description="The value")],
        ) -> int:
            return value
    ```
    """
    return StrawberryArgumentAnnotation(
        description=description,
        name=name,
        deprecation_reason=deprecation_reason,
        directives=directives,
        metadata=metadata,
        graphql_type=graphql_type,
    )


__all__ = [
    "InputContext",
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "argument",
]
