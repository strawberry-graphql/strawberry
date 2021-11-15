from __future__ import annotations

import inspect
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
from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType

from .exceptions import MultipleStrawberryArgumentsError, UnsupportedTypeError
from .scalars import is_scalar
from .types.types import TypeDefinition


if TYPE_CHECKING:
    from strawberry.schema.config import StrawberryConfig


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET: Any = _Unset()


def is_unset(value: Any) -> bool:
    return type(value) is _Unset


class StrawberryArgumentAnnotation:
    description: Optional[str]
    name: Optional[str]

    def __init__(self, description: Optional[str] = None, name: Optional[str] = None):
        self.description = description
        self.name = name


class StrawberryArgument:
    def __init__(
        self,
        python_name: str,
        graphql_name: Optional[str],
        type_annotation: StrawberryAnnotation,
        is_subscription: bool = False,
        description: Optional[str] = None,
        default: object = UNSET,
    ) -> None:
        self.python_name = python_name  # type: ignore
        self.graphql_name = graphql_name
        self.is_subscription = is_subscription
        self.description = description
        self._type: Optional[StrawberryType] = None
        self.type_annotation = type_annotation

        # TODO: Consider moving this logic to a function
        self.default = UNSET if default is inspect.Parameter.empty else default

        if self._annotation_is_annotated(type_annotation):
            self._parse_annotated()

    @property
    def type(self) -> Union[StrawberryType, type]:
        return self.type_annotation.resolve()

    @classmethod
    def _annotation_is_annotated(cls, annotation: StrawberryAnnotation) -> bool:
        return get_origin(annotation.annotation) is Annotated

    def _parse_annotated(self):
        annotated_args = get_args(self.type_annotation.annotation)

        # The first argument to Annotated is always the underlying type
        self.type_annotation = StrawberryAnnotation(annotated_args[0])

        # Find any instances of StrawberryArgumentAnnotation
        # in the other Annotated args, raising an exception if there
        # are multiple StrawberryArgumentAnnotations
        argument_annotation_seen = False
        for arg in annotated_args[1:]:
            if isinstance(arg, StrawberryArgumentAnnotation):
                if argument_annotation_seen:
                    raise MultipleStrawberryArgumentsError(
                        argument_name=self.python_name
                    )

                argument_annotation_seen = True

                self.description = arg.description
                self.graphql_name = arg.name


def convert_argument(
    value: object,
    type_: Union[StrawberryType, type],
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
    config: StrawberryConfig,
) -> object:
    if value is None:
        return None

    if is_unset(value):
        return value

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

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(type_, EnumDefinition):
        return type_.wrapped_cls(value)

    if isinstance(type_, LazyType):
        return convert_argument(value, type_.resolve_type(), scalar_registry, config)

    if hasattr(type_, "_type_definition"):  # TODO: Replace with StrawberryInputObject
        type_definition: TypeDefinition = type_._type_definition  # type: ignore

        assert type_definition.is_input

        kwargs = {}

        for field in type_definition.fields:
            value = cast(Mapping, value)
            graphql_name = config.name_converter.from_field(field)

            if graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[graphql_name], field.type, scalar_registry, config
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
    description: Optional[str] = None, name: Optional[str] = None
) -> StrawberryArgumentAnnotation:
    return StrawberryArgumentAnnotation(description=description, name=name)


# TODO: check exports
__all__ = [
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "UNSET",
    "argument",
    "is_unset",
]
