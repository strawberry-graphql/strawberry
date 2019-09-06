import enum

from dataclasses import is_dataclass

from .str_converters import to_camel_case
from .typing import get_optional_annotation, is_optional


def dict_to_type(dict, cls):
    fields = cls.__dataclass_fields__

    kwargs = {}

    for name, field in fields.items():
        dict_name = name

        if hasattr(field, "field_name") and field.field_name:
            dict_name = field.field_name
        else:
            dict_name = to_camel_case(name)

        annotation = field.type

        if is_optional(annotation):
            annotation = get_optional_annotation(annotation)

        if is_dataclass(annotation):
            kwargs[name] = dict_to_type(dict.get(dict_name, {}), annotation)
        else:
            kwargs[name] = dict.get(dict_name)

            # Convert Enum fields to instances using the value. This is safe
            # because graphql-core has already validated the input.
            if isinstance(annotation, enum.EnumMeta) and kwargs[name]:
                kwargs[name] = annotation(kwargs[name])

    return cls(**kwargs)
