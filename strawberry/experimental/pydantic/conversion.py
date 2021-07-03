from typing import Union, cast

from strawberry.field import StrawberryField
from strawberry.scalars import is_scalar
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType


def _convert_from_pydantic_to_strawberry_type(
    type_: Union[StrawberryType, type], data_from_model=None, extra=None
):
    data = data_from_model if data_from_model is not None else extra

    if isinstance(type_, StrawberryOptional):
        return _convert_from_pydantic_to_strawberry_type(
            type_.of_type, data_from_model=data, extra=extra
        )
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
