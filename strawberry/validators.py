import dataclasses
from typing import Any, Dict, List

from strawberry.arguments import UNSET
from strawberry.field import StrawberryField
from strawberry.types.info import Info


class StrawberryErrorType(BaseException):
    pass


def analyze_errors(errors):
    err = None
    for error in errors:
        if err is None:
            err = error
            continue
        for field in dataclasses.fields(error):
            value = getattr(error, field.name, UNSET)
            if value is not UNSET:
                setattr(err, field.name, value)
    return err


def validate_arguments(kwargs: Dict[str, Any], info: Info):
    errors: List[Any] = []
    for instance in kwargs.values():
        validate_fields(instance, info, errors)
    return analyze_errors(errors)


def validate_fields(instance: Any, info: Info, errors: List[Any]):
    if not hasattr(instance, "_type_definition"):
        return
    for field in instance._type_definition.fields:
        if not field.validators:
            continue
        value = getattr(instance, field.name)
        try:
            value = validate_field(field, value, info)
        except StrawberryErrorType as e:
            errors.append(e)
            continue
        setattr(instance, field.name, value)


def validate_field(field: StrawberryField, value: Any, info: Info) -> Any:
    for validator in field.validators:
        value = validator(value=value, info=info)
    return value
