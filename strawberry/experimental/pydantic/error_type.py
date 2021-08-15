import dataclasses
from typing import Any, List, Optional, Type

from pydantic import BaseModel
from pydantic.fields import ModelField

from strawberry.experimental.pydantic.utils import (
    get_strawberry_type_from_model,
    normalize_type,
)
from strawberry.object_type import _process_type
from strawberry.types.types import FederationTypeParams
from strawberry.utils.typing import get_list_annotation, is_list


def get_type_for_field(field: ModelField):
    type_ = field.outer_type_
    type_ = normalize_type(type_)
    return field_type_to_type(type_)


def field_type_to_type(type_):
    error_class: Any = str
    strawberry_type: Any = error_class

    if is_list(type_):
        child_type = get_list_annotation(type_)

        if is_list(child_type):
            strawberry_type = field_type_to_type(child_type)
        elif issubclass(child_type, BaseModel):
            strawberry_type = get_strawberry_type_from_model(child_type)
        else:
            strawberry_type = List[error_class]

        strawberry_type = Optional[strawberry_type]
    elif issubclass(type_, BaseModel):
        strawberry_type = get_strawberry_type_from_model(type_)
        return Optional[strawberry_type]

    return Optional[List[strawberry_type]]


def error_type(
    model: Type[BaseModel],
    *,
    fields: List[str],
    name: Optional[str] = None,
    description: Optional[str] = None,
    federation: Optional[FederationTypeParams] = None,
):
    def wrap(cls):
        model_fields = model.__fields__
        fields_set = set(fields)

        cls = dataclasses.make_dataclass(
            cls.__name__,
            [
                (
                    name,
                    get_type_for_field(field),
                    dataclasses.field(default=None),  # type: ignore
                )
                for name, field in model_fields.items()
                if name in fields_set
            ],
        )

        _process_type(
            cls,
            name=name,
            is_input=False,
            is_interface=False,
            description=description,
            federation=federation,
        )

        model._strawberry_type = cls  # type: ignore
        return cls

    return wrap
