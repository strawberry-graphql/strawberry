from dataclasses import is_dataclass


def dict_to_type(dict, cls):
    fields = cls.__dataclass_fields__

    kwargs = {}

    for name, field in fields.items():
        if is_dataclass(field.type):
            kwargs[name] = dict_to_type(dict.get(name, {}), field.type)
        else:
            kwargs[name] = dict.get(name)

    return cls(**kwargs)
