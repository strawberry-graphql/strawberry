from __future__ import annotations

import inspect
import warnings
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
    has_object_definition,
)
from strawberry.types.enum import StrawberryEnumDefinition, has_enum_definition
from strawberry.types.lazy_type import LazyType, StrawberryLazyReference
from strawberry.types.maybe import Some
from strawberry.types.unset import UNSET as _deprecated_UNSET  # noqa: N811
from strawberry.types.unset import (
    _deprecated_is_unset,  # noqa: F401
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from strawberry.schema.config import StrawberryConfig
    from strawberry.types.base import StrawberryType
    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper


DEPRECATED_NAMES: dict[str, str] = {
    "UNSET": (
        "importing `UNSET` from `strawberry.arguments` is deprecated, "
        "import instead from `strawberry` or from `strawberry.types.unset`"
    ),
    "is_unset": "`is_unset` is deprecated use `value is UNSET` instead",
}


class StrawberryArgumentAnnotation:
    description: str | None
    name: str | None
    deprecation_reason: str | None
    directives: Iterable[object]
    metadata: Mapping[Any, Any]
    graphql_type: Any | None

    def __init__(
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
    def __init__(
        self,
        python_name: str,
        graphql_name: str | None,
        type_annotation: StrawberryAnnotation,
        is_subscription: bool = False,
        description: str | None = None,
        default: object = _deprecated_UNSET,
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
        self.directives = directives
        self.metadata = metadata or {}

        # TODO: Consider moving this logic to a function
        self.default = (
            _deprecated_UNSET if default is inspect.Parameter.empty else default
        )

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
                        self.directives = arg.directives
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


def convert_argument(
    value: object,
    type_: StrawberryType | type,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    config: StrawberryConfig,
) -> object:
    from strawberry.relay.types import GlobalID

    # TODO: move this somewhere else and make it first class
    # Handle StrawberryMaybe first, since it extends StrawberryOptional
    if isinstance(type_, StrawberryMaybe):
        # Check if this is Maybe[T | None] (has StrawberryOptional as of_type)
        if isinstance(type_.of_type, StrawberryOptional):
            # This is Maybe[T | None] - allows null values
            res = convert_argument(value, type_.of_type, scalar_registry, config)

            return Some(res)

        if value is None:
            from strawberry.exceptions import StrawberryGraphQLError

            type_name = getattr(type_.of_type, "__name__", str(type_.of_type))
            raise StrawberryGraphQLError(
                f"Expected value of type '{type_name}', found null. "
                f"Field of type 'Maybe[{type_name}]' cannot be explicitly set to null. "
                f"Use 'Maybe[{type_name} | None]' if you need to allow null values."
            )

        # This is Maybe[T] - validation for null values is handled by MaybeNullValidationRule
        # Convert the value and wrap in Some()
        res = convert_argument(value, type_.of_type, scalar_registry, config)

        return Some(res)

    # Handle regular StrawberryOptional (not Maybe)
    if isinstance(type_, StrawberryOptional):
        return convert_argument(value, type_.of_type, scalar_registry, config)

    if value is None:
        return None

    if value is _deprecated_UNSET:
        return _deprecated_UNSET

    if isinstance(type_, StrawberryList):
        value_list = cast("Iterable", value)

        if _is_leaf_type(
            type_.of_type, scalar_registry, skip_classes=(GlobalID,)
        ) or _is_optional_leaf_type(
            type_.of_type, scalar_registry, skip_classes=(GlobalID,)
        ):
            return value_list

        value_list = cast("Iterable", value)

        return [
            convert_argument(x, type_.of_type, scalar_registry, config)
            for x in value_list
        ]

    if _is_leaf_type(type_, scalar_registry):
        if type_ is GlobalID:
            return GlobalID.from_id(value)  # type: ignore

        return value

    if isinstance(type_, LazyType):
        return convert_argument(value, type_.resolve_type(), scalar_registry, config)

    if has_enum_definition(type_):
        enum_definition: StrawberryEnumDefinition = type_.__strawberry_definition__
        return convert_argument(value, enum_definition, scalar_registry, config)

    if has_object_definition(type_):
        kwargs = {}

        type_definition = type_.__strawberry_definition__
        for field in type_definition.fields:
            value = cast("Mapping", value)
            graphql_name = config.name_converter.from_field(field)

            if graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[graphql_name],
                    field.resolve_type(type_definition=type_definition),
                    scalar_registry,
                    config,
                )

        type_ = cast("type", type_)
        return type_(**kwargs)

    raise UnsupportedTypeError(type_)


def convert_arguments(
    value: dict[str, Any],
    arguments: list[StrawberryArgument],
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
    config: StrawberryConfig,
) -> dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values.
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
            )

    return kwargs


def argument(
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
    import strawberry


    @strawberry.type
    class Query:
        @strawberry.field
        def example(
            self, info, value: int = strawberry.argument(description="The value")
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


def __getattr__(name: str) -> Any:
    if name in DEPRECATED_NAMES:
        warnings.warn(DEPRECATED_NAMES[name], DeprecationWarning, stacklevel=2)
        return globals()[f"_deprecated_{name}"]
    raise AttributeError(f"module {__name__} has no attribute {name}")


# TODO: check exports
__all__ = [  # noqa: F822
    "UNSET",  # for backwards compatibility  # type: ignore
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "argument",
    "is_unset",  # for backwards compatibility  # type: ignore
]
