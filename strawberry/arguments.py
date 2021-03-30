import enum
import inspect
from typing import Any, Dict, List, Mapping, Optional, Type, cast

from typing_extensions import Annotated, get_args, get_origin

from .exceptions import MultipleStrawberryArgumentsError, UnsupportedTypeError
from .scalars import is_scalar
from .types.types import ArgumentDefinition, undefined
from .utils.str_converters import to_camel_case


class StrawberryArgument:
    description: Optional[str]

    def __init__(self, description: Optional[str] = None):
        self.description = description


def get_arguments_from_annotations(
    annotations: Any, parameters: Mapping[str, inspect.Parameter], origin: Any
) -> List[ArgumentDefinition]:
    arguments = []

    for name, annotation in annotations.items():
        default_value = parameters[name].default
        default_value = (
            undefined
            if default_value is inspect.Parameter.empty or is_unset(default_value)
            else default_value
        )

        argument_definition = ArgumentDefinition(
            origin_name=name,
            name=to_camel_case(name),
            origin=origin,
            default_value=default_value,
        )

        if get_origin(annotation) is Annotated:
            annotated_args = get_args(annotation)

            # The first argument to Annotated is always the underlying type
            argument_definition.type = annotated_args[0]

            argument_metadata = None
            # Find any instances of StrawberryArgument in the other Annotated args,
            # raising an exception if there are multiple StrawberryArguments
            for arg in annotated_args[1:]:
                if isinstance(arg, StrawberryArgument):
                    if argument_metadata is not None:
                        raise MultipleStrawberryArgumentsError(
                            field_name=origin.__name__, argument_name=name
                        )
                    argument_metadata = arg

            if argument_metadata is not None:
                argument_definition.description = argument_metadata.description
        else:
            argument_definition.type = annotation

        arguments.append(argument_definition)

        # Deferred to prevent import cycles
        from .types.type_resolver import _resolve_type

        _resolve_type(argument_definition)

    return arguments


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET: Any = _Unset()


def is_unset(value: Any) -> bool:
    return type(value) is _Unset


def convert_argument(value: Any, argument_definition: ArgumentDefinition) -> Any:
    if value is None:
        return None

    if is_unset(value):
        return value

    if argument_definition.is_list:
        child_definition = cast(ArgumentDefinition, argument_definition.child)

        return [convert_argument(x, child_definition) for x in value]

    argument_type = cast(Type, argument_definition.type)

    if is_scalar(argument_type):
        return value

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(argument_type, enum.EnumMeta):
        return argument_type(value)  # type: ignore

    if hasattr(argument_type, "_type_definition"):
        assert argument_type._type_definition.is_input

        kwargs = {}

        for field in argument_type._type_definition.fields:
            if field.graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[field.graphql_name], field
                )

        return argument_type(**kwargs)

    raise UnsupportedTypeError(argument_type)


def convert_arguments(
    value: Dict[str, Any],
    arguments: List[ArgumentDefinition],
) -> Dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values."""

    if not arguments:
        return {}

    kwargs = {}

    for argument in arguments:
        if argument.name in value:
            origin_name = cast(str, argument.origin_name)
            current_value = value[argument.name]

            kwargs[origin_name] = convert_argument(current_value, argument)

    return kwargs


def argument(description: Optional[str] = None) -> StrawberryArgument:
    return StrawberryArgument(description=description)


__all__ = [
    "ArgumentDefinition",
    "StrawberryArgument",
    "UNSET",
    "argument",
    "convert_argument",
    "convert_arguments",
    "get_arguments_from_annotations",
    "is_unset",
    "undefined",
]
