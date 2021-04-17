from typing import cast

from strawberry.field import StrawberryField
from strawberry.scalars import is_scalar


def _convert_from_pydantic_to_strawberry_field(
    field: StrawberryField, data_from_model=None, extra=None
):
    data = data_from_model if data_from_model is not None else extra

    if field.is_list:
        assert field.child is not None

        items = [None for _ in data]

        for index, item in enumerate(data):
            items[index] = _convert_from_pydantic_to_strawberry_field(
                field.child,
                data_from_model=item,
                extra=extra[index] if extra else None,
            )

        return items
    elif is_scalar(field.type):  # type: ignore
        return data
    else:
        return convert_pydantic_model_to_strawberry_class(
            field.type, model_instance=data_from_model, extra=extra
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
        kwargs[python_name] = _convert_from_pydantic_to_strawberry_field(
            field, data_from_model, extra=data_from_extra
        )

    return cls(**kwargs)
