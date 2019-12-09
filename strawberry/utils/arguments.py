import enum
from datetime import date, datetime, time

from dataclasses import is_dataclass

from ..exceptions import UnsupportedTypeError
from .str_converters import to_camel_case, to_snake_case
from .typing import get_list_annotation, get_optional_annotation, is_list, is_optional


SCALAR_TYPES = [int, str, float, bytes, bool, datetime, date, time]


def _to_type(value, annotation):
    if value is None:
        return None

    if is_optional(annotation):
        annotation = get_optional_annotation(annotation)

    # TODO: change this to be a is_scalar util and make sure it works with any scalar
    if getattr(annotation, "__supertype__", annotation) in SCALAR_TYPES:
        return value

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(annotation, enum.EnumMeta):
        return annotation(value)

    if is_list(annotation):
        annotation = get_list_annotation(annotation)

        return [_to_type(x, annotation) for x in value]

    if is_dataclass(annotation):
        fields = annotation.__dataclass_fields__

        kwargs = {}

        for name, field in fields.items():
            dict_name = name

            if hasattr(field, "field_name") and field.field_name:
                dict_name = field.field_name
            else:
                dict_name = to_camel_case(name)

            kwargs[name] = _to_type(value.get(dict_name), field.type)

        return annotation(**kwargs)

    raise UnsupportedTypeError(annotation)


def convert_args(args, annotations):
    """Converts a nested dictionary to a dictionary of strawberry input types."""

    converted_args = {}

    for key, value in args.items():
        key = to_snake_case(key)
        annotation = annotations[key]

        converted_args[key] = _to_type(value, annotation)

    return converted_args
