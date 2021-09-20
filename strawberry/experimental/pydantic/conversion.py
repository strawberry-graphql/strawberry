from typing import Union, cast

from strawberry.enum import EnumDefinition
from strawberry.field import StrawberryField
from strawberry.scalars import is_scalar
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.union import StrawberryUnion


def _convert_from_pydantic_to_strawberry_type(
    type_: Union[StrawberryType, type], data_from_model=None, extra=None
):
    data = data_from_model if data_from_model is not None else extra

    if isinstance(type_, StrawberryOptional):
        if data is None:
            return data
        return _convert_from_pydantic_to_strawberry_type(
            type_.of_type, data_from_model=data, extra=extra
        )
    if isinstance(type_, StrawberryUnion):
        for option_type in type_.types:
            if hasattr(option_type, "_pydantic_type"):
                source_type = option_type._pydantic_type  # type: ignore
            else:
                source_type = cast(type, option_type)
            if isinstance(data, source_type):
                return _convert_from_pydantic_to_strawberry_type(
                    option_type, data_from_model=data, extra=extra
                )
    if isinstance(type_, EnumDefinition):
        return data
    if isinstance(type_, StrawberryList):
        items = []
        for index, item in enumerate(data):
            items.append(
                _convert_from_pydantic_to_strawberry_type(
                    type_.of_type,
                    data_from_model=item,
                    extra=extra[index] if extra else None,
                )
            )

        return items
    elif is_scalar(type_):
        return data
    else:
        # in the case of an interface, the concrete type may be more specific
        # than the type in the field definition
        if hasattr(type(data), "_strawberry_type"):
            type_ = type(data)._strawberry_type
        return convert_pydantic_model_to_strawberry_class(
            type_, model_instance=data_from_model, extra=extra
        )


def convert_pydantic_model_to_strawberry_class(cls, *, model_instance=None, extra=None):
    extra = extra or {}
    kwargs = {}

    for field in cls._type_definition.fields:
        field = cast(StrawberryField, field)
        python_name = field.python_name

        data_from_extra = extra.get(python_name, None)
        data_from_model = (
            getattr(model_instance, python_name, None) if model_instance else None
        )
        kwargs[python_name] = _convert_from_pydantic_to_strawberry_type(
            field.type, data_from_model, extra=data_from_extra
        )

    return cls(**kwargs)
