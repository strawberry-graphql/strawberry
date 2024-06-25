from __future__ import annotations

import inspect
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Union,
    cast,
)
from typing_extensions import Annotated, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType, StrawberryLazyReference
from strawberry.type import StrawberryList, StrawberryOptional, has_object_definition

from .exceptions import MultipleStrawberryArgumentsError, UnsupportedTypeError
from .scalars import is_scalar
from .unset import UNSET as _deprecated_UNSET
from .unset import _deprecated_is_unset  # noqa # type: ignore

if TYPE_CHECKING:
    from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
    from strawberry.schema.config import StrawberryConfig
    from strawberry.type import StrawberryType


DEPRECATED_NAMES: Dict[str, str] = {
    "UNSET": (
        "importing `UNSET` from `strawberry.arguments` is deprecated, "
        "import instead from `strawberry` or from `strawberry.unset`"
    ),
    "is_unset": "`is_unset` is deprecated use `value is UNSET` instead",
}


class StrawberryArgumentAnnotation:
    description: Optional[str]
    name: Optional[str]
    deprecation_reason: Optional[str]
    directives: Iterable[object]
    metadata: Mapping[Any, Any]

    def __init__(
        self,
        description: Optional[str] = None,
        name: Optional[str] = None,
        deprecation_reason: Optional[str] = None,
        directives: Iterable[object] = (),
        metadata: Optional[Mapping[Any, Any]] = None,
    ) -> None:
        self.description = description
        self.name = name
        self.deprecation_reason = deprecation_reason
        self.directives = directives
        self.metadata = metadata or {}


class StrawberryArgument:
    def __init__(
        self,
        python_name: str,
        graphql_name: Optional[str],
        type_annotation: StrawberryAnnotation,
        is_subscription: bool = False,
        description: Optional[str] = None,
        default: object = _deprecated_UNSET,
        deprecation_reason: Optional[str] = None,
        directives: Iterable[object] = (),
        metadata: Optional[Mapping[Any, Any]] = None,
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

                    if isinstance(arg, StrawberryLazyReference):
                        self.type_annotation = StrawberryAnnotation(
                            arg.resolve_forward_ref(first)
                        )

    @property
    def type(self) -> Union[StrawberryType, type]:
        return self.type_annotation.resolve()

    @property
    def is_graphql_generic(self) -> bool:
        from strawberry.schema.compat import is_graphql_generic

        return is_graphql_generic(self.type)


def convert_argument(
    value: object,
    type_: Union[StrawberryType, type],
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
    config: StrawberryConfig,
) -> object:
    # TODO: move this somewhere else and make it first class

    if value is None:
        return None

    if value is _deprecated_UNSET:
        return _deprecated_UNSET

    if isinstance(type_, StrawberryOptional):
        return convert_argument(value, type_.of_type, scalar_registry, config)

    if isinstance(type_, StrawberryList):
        value_list = cast(Iterable, value)
        return [
            convert_argument(x, type_.of_type, scalar_registry, config)
            for x in value_list
        ]

    if is_scalar(type_, scalar_registry):
        return value

    if isinstance(type_, EnumDefinition):
        return value

    if isinstance(type_, LazyType):
        return convert_argument(value, type_.resolve_type(), scalar_registry, config)

    if hasattr(type_, "_enum_definition"):
        enum_definition: EnumDefinition = type_._enum_definition
        return convert_argument(value, enum_definition, scalar_registry, config)

    if has_object_definition(type_):
        kwargs = {}

        type_definition = type_.__strawberry_definition__
        for field in type_definition.fields:
            value = cast(Mapping, value)
            graphql_name = config.name_converter.from_field(field)

            if graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[graphql_name],
                    field.resolve_type(type_definition=type_definition),
                    scalar_registry,
                    config,
                )

        type_ = cast(type, type_)
        return type_(**kwargs)

    raise UnsupportedTypeError(type_)


def convert_arguments(
    value: Dict[str, Any],
    arguments: List[StrawberryArgument],
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
    config: StrawberryConfig,
) -> Dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values."""

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
    description: Optional[str] = None,
    name: Optional[str] = None,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
    metadata: Optional[Mapping[Any, Any]] = None,
) -> StrawberryArgumentAnnotation:
    return StrawberryArgumentAnnotation(
        description=description,
        name=name,
        deprecation_reason=deprecation_reason,
        directives=directives,
        metadata=metadata,
    )


def __getattr__(name: str) -> Any:
    if name in DEPRECATED_NAMES:
        warnings.warn(DEPRECATED_NAMES[name], DeprecationWarning, stacklevel=2)
        return globals()[f"_deprecated_{name}"]
    raise AttributeError(f"module {__name__} has no attribute {name}")


# TODO: check exports
__all__ = [  # noqa: F822
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "UNSET",  # for backwards compatibility  # type: ignore
    "argument",
    "is_unset",  # for backwards compatibility  # type: ignore
]
