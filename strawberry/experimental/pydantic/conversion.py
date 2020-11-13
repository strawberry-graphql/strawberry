from typing import cast

from strawberry.scalars import is_scalar
from strawberry.types.types import FieldDefinition


def _convert_from_pydantic_to_strawberry_field(
    field: FieldDefinition, data_from_model=None, extra=None
):
    data = data_from_model or extra

    if field.is_list:
        child = field.child
        items = [None for _ in data]

        for index, item in enumerate(data):
            items[index] = _convert_from_pydantic_to_strawberry_field(
                cast(FieldDefinition, child),
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
        field = cast(FieldDefinition, field)
        origin_name = field.origin_name

        data_from_extra = extra.get(origin_name, None)
        data_from_model = (
            getattr(model_instance, origin_name, None) if model_instance else None
        )
        kwargs[origin_name] = _convert_from_pydantic_to_strawberry_field(
            field, data_from_model, extra=data_from_extra
        )

    return cls(**kwargs)
