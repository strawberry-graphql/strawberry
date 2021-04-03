from typing import Any, Dict

from strawberry.field import StrawberryField
from strawberry.types.info import Info


def validate_arguments(kwargs: Dict[str, Any], info: Info):
    for instance in kwargs.values():
        validate_fields(instance, info)


def validate_fields(instance: Any, info: Info):
    if not hasattr(instance, "_type_definition"):
        return
    for field in instance._type_definition.fields:
        if not field.validators:
            continue
        value = getattr(instance, field.name)
        value = validate_field(field, value, info)
        setattr(instance, field.name, value)


def validate_field(field: StrawberryField, value: Any, info: Info) -> Any:
    for validator in field.validators:
        value = validator(value=value, info=info)
    return value
