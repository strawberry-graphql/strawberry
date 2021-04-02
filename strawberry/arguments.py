import enum
import inspect
from typing import Any, Dict, List, Mapping, Optional, Type, Union, cast

from typing_extensions import Annotated, get_args, get_origin

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
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
        type: Optional[Union[Type, StrawberryUnion]] = None,
        origin: Optional[Type] = None,
        child: Optional["StrawberryArgument"] = None,
        is_subscription: bool = False,
        is_optional: bool = False,
        is_child_optional: bool = False,
        is_list: bool = False,
        is_union: bool = False,
        description: Optional[str] = None,
        default_value: Any = undefined,
    ) -> None:
        self.python_name = python_name
        self._graphql_name = graphql_name
        self.type = type
        self.origin = origin
        self.child = child
        self.is_subscription = is_subscription
        self.is_optional = is_optional
        self.is_child_optional = is_child_optional
        self.is_list = is_list
        self.is_union = is_union
        self.description = description
        self.default_value = default_value

    @property
    def graphql_name(self) -> Optional[str]:
        return self._graphql_name


def get_arguments_from_annotations(
    annotations: Any, parameters: Mapping[str, inspect.Parameter], origin: Any
) -> List[StrawberryArgument]:
    arguments = []

    for name, annotation in annotations.items():
        default_value = parameters[name].default
        default_value = (
            undefined
            if default_value is inspect.Parameter.empty or is_unset(default_value)
            else default_value
        )

        argument_definition = StrawberryArgument(
            python_name=name,
            graphql_name=to_camel_case(name),
            origin=origin,
            default_value=default_value,
        )

        if get_origin(annotation) is Annotated:
            annotated_args = get_args(annotation)

            # The first argument to Annotated is always the underlying type
            argument_definition.type = annotated_args[0]

            argument_metadata = None
            # Find any instances of StrawberryArgumentAnnotation
            # in the other Annotated args, raising an exception if there
            # are multiple StrawberryArgumentAnnotations
            for arg in annotated_args[1:]:
                if isinstance(arg, StrawberryArgumentAnnotation):
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


def convert_argument(value: Any, argument_definition: StrawberryArgument) -> Any:
    if value is None:
        return None

    if is_unset(value):
        return value

    if argument_definition.is_list:
        child_definition = cast(StrawberryArgument, argument_definition.child)

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
            assert argument.python_name

            current_value = value[argument.graphql_name]

            kwargs[argument.python_name] = convert_argument(current_value, argument)

    return kwargs


def argument(description: Optional[str] = None) -> StrawberryArgumentAnnotation:
    return StrawberryArgumentAnnotation(description=description)


# TODO: check exports
__all__ = [
    "StrawberryArgumentAnnotation",
    "UNSET",
    "argument",
    "convert_argument",
    "convert_arguments",
    "get_arguments_from_annotations",
    "is_unset",
    "undefined",
]
