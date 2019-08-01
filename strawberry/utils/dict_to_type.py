from dataclasses import is_dataclass

from .str_converters import to_camel_case


def dict_to_type(dict, cls):
    fields = cls.__dataclass_fields__

    kwargs = {}

    for name, field in fields.items():
        dict_name = name

        if hasattr(field, "field_name") and field.field_name:
            dict_name = field.field_name
        else:
            dict_name = to_camel_case(name)

        if is_dataclass(field.type):
            kwargs[name] = dict_to_type(dict.get(dict_name, {}), field.type)
        else:
            kwargs[name] = dict.get(dict_name)

    return cls(**kwargs)
