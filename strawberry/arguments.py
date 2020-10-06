import enum
import inspect
from typing import Any, Callable, Dict, List, Mapping, Type, cast

from .exceptions import MissingArgumentsAnnotationsError, UnsupportedTypeError
from .scalars import is_scalar
from .types.type_resolver import resolve_type
from .types.types import ArgumentDefinition, undefined
from .utils.str_converters import to_camel_case


def get_arguments_from_annotations(
    annotations: Any, parameters: Mapping[str, inspect.Parameter], origin: Any
) -> List[ArgumentDefinition]:
    arguments = []

    for name, annotation in annotations.items():
        default_value = parameters[name].default
        default_value = (
            undefined
            if default_value in (inspect._empty, None)  # type: ignore
            else default_value
        )

        argument_definition = ArgumentDefinition(
            origin_name=name,
            name=to_camel_case(name),
            origin=origin,
            type=annotation,
            default_value=default_value,
        )

        arguments.append(argument_definition)

        resolve_type(argument_definition)

    return arguments


def get_arguments_from_resolver(resolver: Callable) -> List[ArgumentDefinition]:
    annotations = resolver.__annotations__
    parameters = inspect.signature(resolver).parameters
    function_arguments = set(parameters) - {"root", "self", "info"}

    annotations = {
        name: annotation
        for name, annotation in annotations.items()
        if name not in ["root", "info", "return", "self"]
    }

    annotated_function_arguments = set(annotations.keys())
    arguments_missing_annotations = function_arguments - annotated_function_arguments

    if len(arguments_missing_annotations) > 0:
        raise MissingArgumentsAnnotationsError(
            resolver.__name__, arguments_missing_annotations
        )

    return get_arguments_from_annotations(annotations, parameters, origin=resolver)


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
            if field.name in value:
                kwargs[field.origin_name] = convert_argument(value[field.name], field)

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
