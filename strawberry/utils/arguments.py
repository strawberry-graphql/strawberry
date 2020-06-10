import enum
import typing
from dataclasses import is_dataclass
from datetime import date, datetime, time
from decimal import Decimal

from ..exceptions import UnsupportedTypeError
from .str_converters import to_camel_case
from .typing import get_list_annotation, get_optional_annotation, is_list, is_optional


# TODO: these need to be update when defining a custom scalar
SCALAR_TYPES = [int, str, float, bytes, bool, datetime, date, time, Decimal]


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET = _Unset()


def is_unset(value: typing.Any) -> bool:
    return value is UNSET


def convert_args(
    value: typing.Union[typing.Dict[str, typing.Any], typing.Any],
    annotation: typing.Union[typing.Dict[str, typing.Type], typing.Type],
):
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values."""

    if annotation == {}:
        return value

    if value is None:
        return None

    if is_unset(value):
        return value

    if is_optional(annotation):
        annotation = get_optional_annotation(annotation)

    # TODO: change this to be a is_scalar util and make sure it works with any scalar
    if getattr(annotation, "__supertype__", annotation) in SCALAR_TYPES:
        return value

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(annotation, enum.EnumMeta):
        return annotation(value)  # type: ignore

    if is_list(annotation):
        annotation = get_list_annotation(annotation)

        return [convert_args(x, annotation) for x in value]

    fields = None

    # we receive dicts when converting resolvers arguments to
    # actual types
    if isinstance(annotation, dict):
        fields = annotation.items()

    elif is_dataclass(annotation):
        fields = annotation.__dataclass_fields__.items()

    if fields:
        kwargs = {}

        for name, field in fields:
            dict_name = name

            if hasattr(field, "field_name") and field.field_name:
                dict_name = field.field_name
            else:
                dict_name = to_camel_case(name)

            # dataclasses field have a .type attribute
            if hasattr(field, "type"):
                field_type = field.type
            # meanwhile when using dicts the value of the field is
            # the actual type, for example in: { 'name': str }
            else:
                field_type = field

            if dict_name in value:
                kwargs[name] = convert_args(value[dict_name], field_type)

        if is_dataclass(annotation):
            return annotation(**kwargs)  # type: ignore

        return kwargs

    raise UnsupportedTypeError(annotation)
