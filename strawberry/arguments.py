from __future__ import annotations

import enum
import inspect
import sys
import typing
from typing import Any, Dict, List, Mapping, Optional, Type, Iterable

from typing_extensions import Annotated, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.type import StrawberryType, StrawberryList, StrawberryOptional

from .exceptions import MultipleStrawberryArgumentsError, UnsupportedTypeError
from .scalars import is_scalar
from .types.types import undefined
from .union import StrawberryUnion
from .utils.str_converters import to_camel_case


class StrawberryArgumentAnnotation:
    description: Optional[str]

    def __init__(self, description: Optional[str] = None):
        self.description = description


class StrawberryArgument:
    def __init__(
        self,
        # TODO: this optional will probably go away when we have StrawberryList
        python_name: Optional[str],
        graphql_name: Optional[str],
        type_annotation: Optional[StrawberryAnnotation],
        origin: Optional[Type] = None,
        is_subscription: bool = False,
        description: Optional[str] = None,
        default_value: Any = undefined,
    ) -> None:
        self.python_name = python_name
        self._graphql_name = graphql_name
        self.type_annotation = type_annotation
        self.origin = origin
        self.is_subscription = is_subscription
        self.description = description
        self.default_value = default_value

        self._type: Optional[StrawberryType] = None

    @property
    def graphql_name(self) -> Optional[str]:
        if self._graphql_name:
            return self._graphql_name
        if self.python_name:
            return to_camel_case(self.python_name)
        return None

    @classmethod
    def from_annotated(
        cls,
        python_name: str,
        annotation: Type[Annotated],  # type: ignore
        default_value: Any,
        origin: Any,
    ) -> StrawberryArgument:
        annotated_args = get_args(annotation)

        # The first argument to Annotated is always the underlying type
        type_ = annotated_args[0]
        argument_metadata = None
        argument_description = None

        # Find any instances of StrawberryArgumentAnnotation
        # in the other Annotated args, raising an exception if there
        # are multiple StrawberryArgumentAnnotations
        for arg in annotated_args[1:]:
            if isinstance(arg, StrawberryArgumentAnnotation):
                if argument_metadata is not None:
                    raise MultipleStrawberryArgumentsError(
                        field_name=origin.__name__, argument_name=python_name
                    )

                argument_metadata = arg

        if argument_metadata is not None:
            argument_description = argument_metadata.description

        return cls(
            type_annotation=type_,
            description=argument_description,
            python_name=python_name,
            # TODO: fetch from StrawberryArgumentAnnotation
            graphql_name=None,
            default_value=default_value,
        )

    @property
    def type(self) -> StrawberryType:
        return self.type_annotation.resolve()


def get_arguments_from_annotations(
    annotations: Any, parameters: Mapping[str, inspect.Parameter], origin: object
) -> List[StrawberryArgument]:

    arguments = []

    for name, annotation in annotations.items():
        default_value = parameters[name].default
        default_value = (
            undefined
            if default_value is inspect.Parameter.empty or is_unset(default_value)
            else default_value
        )

        module = sys.modules[origin.__module__]

        strawberry_annotation = StrawberryAnnotation(
            annotation=annotation,
            namespace=module.__dict__,
        )

        if get_origin(annotation) is Annotated:
            argument = StrawberryArgument.from_annotated(
                python_name=name,
                annotation=strawberry_annotation,
                default_value=default_value,
                origin=origin,
            )
        else:
            argument = StrawberryArgument(
                type_annotation=strawberry_annotation,
                python_name=name,
                graphql_name=None,
                default_value=default_value,
                description=None,
                origin=origin,
            )

        argument.type = argument.type_annotation.resolve()

        arguments.append(argument)

    return arguments


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET: Any = _Unset()


def is_unset(value: Any) -> bool:
    return type(value) is _Unset


def convert_argument(value: object, type_: StrawberryType) -> object:
    if value is None:
        return None

    if is_unset(value):
        return value

    if isinstance(type_, StrawberryOptional):
        return convert_argument(value, type_.of_type)

    if isinstance(type_, StrawberryList):
        value_list = typing.cast(Iterable, value)
        return [convert_argument(x, type_.of_type) for x in value_list]

    if is_scalar(type_):
        return value

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(type_, enum.EnumMeta):
        return type_(value)  # type: ignore

    if hasattr(type_, "_type_definition"):  # TODO: Replace with StrawberryInputObject
        assert type_._type_definition.is_input

        kwargs = {}

        for field in type_._type_definition.fields:
            # TODO: cast value as a protocol that supports __getitem__
            if field.graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[field.graphql_name], field.type
                )

        return type_(**kwargs)

    raise UnsupportedTypeError(type_)


def convert_arguments(
    value: Dict[str, Any],
    arguments: List[StrawberryArgument],
) -> Dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values."""

    if not arguments:
        return {}

    kwargs = {}

    for argument in arguments:
        if argument.graphql_name in value:
            current_value = value[argument.graphql_name]
            kwargs[argument.python_name] = convert_argument(
                value=current_value,
                type_=argument.type,
            )

    return kwargs


def argument(description: Optional[str] = None) -> StrawberryArgumentAnnotation:
    return StrawberryArgumentAnnotation(description=description)


# TODO: check exports
__all__ = [
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "UNSET",
    "argument",
    "get_arguments_from_annotations",
    "is_unset",
    "undefined",
]
