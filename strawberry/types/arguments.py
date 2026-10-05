from __future__ import annotations

import dataclasses
import inspect
from dataclasses import MISSING
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
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
    has_object_definition,
)
from strawberry.types.enum import StrawberryEnumDefinition, has_enum_definition
from strawberry.types.lazy_type import LazyType, StrawberryLazyReference
from strawberry.types.maybe import Some
from strawberry.types.unset import UNSET

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

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

        # TODO: Consider moving this logic to a function
        self.default = UNSET if default is inspect.Parameter.empty else default

        annotation = type_annotation.annotation
        if not isinstance(annotation, str):
            resolved_annotation = annotation
            if get_origin(resolved_annotation) is Annotated:
                first, *rest = get_args(resolved_annotation)

                # The first argument to Annotated is always the underlying type
                self.type_annotation = StrawberryAnnotation(first)

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
                        self.type_annotation = StrawberryAnnotation(
                            arg.resolve_forward_ref(first)
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
    if not arguments:
        return {}

    kwargs = {}

    for argument in arguments:
        assert argument.python_name

        name = config.name_converter.from_argument(argument)

        if name in value:
            current_value = value[name]

            kwargs[argument.python_name] = convert_argument(
                value=current_value,
                type_=argument.type,
                config=config,
                scalar_registry=scalar_registry,
                info=info,
                path=(name,),
            )

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
