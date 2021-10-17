import dataclasses
import warnings
from typing import Any, List, Optional, Sequence, Tuple, Type, cast

from pydantic import BaseModel
from pydantic.fields import ModelField

import strawberry
from strawberry.experimental.pydantic.utils import (
    get_private_fields,
    get_strawberry_type_from_model,
    normalize_type,
)
from strawberry.object_type import _process_type, _wrap_dataclass
from strawberry.schema_directive import StrawberrySchemaDirective
from strawberry.types.type_resolver import _get_fields
from strawberry.utils.typing import get_list_annotation, is_list

from .exceptions import MissingFieldsListError


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
    fields: List[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[StrawberrySchemaDirective]] = (),
    all_fields: bool = False
):
    def wrap(cls):
        model_fields = model.__fields__
        fields_set = set(fields) if fields else set([])

        if fields:
            warnings.warn(
                "`fields` is deprecated, use `auto` type annotations instead",
                DeprecationWarning,
            )

        existing_fields = getattr(cls, "__annotations__", {})
        fields_set = fields_set.union(
            set(name for name, typ in existing_fields.items() if typ == strawberry.auto)
        )

        if all_fields:
            if fields_set:
                warnings.warn(
                    "Using all_fields overrides any explicitly defined fields "
                    "in the model, using both is likely a bug",
                    stacklevel=2,
                )
            fields_set = set(model_fields.keys())

        if not fields_set:
            raise MissingFieldsListError(cls)

        all_model_fields: List[Tuple[str, Any, dataclasses.Field]] = [
            (
                name,
                get_type_for_field(field),
                dataclasses.field(default=None),  # type: ignore
            )
            for name, field in model_fields.items()
            if name in fields_set
        ]

        wrapped = _wrap_dataclass(cls)
        extra_fields = cast(List[dataclasses.Field], _get_fields(wrapped))
        private_fields = get_private_fields(wrapped)

        all_model_fields.extend(
            (
                (
                    field.name,
                    field.type,
                    field,
                )
                for field in extra_fields + private_fields
                if field.type != strawberry.auto
            )
        )

        cls = dataclasses.make_dataclass(
            cls.__name__,
            all_model_fields,
            bases=cls.__bases__,
        )

        _process_type(
            cls,
            name=name,
            is_input=False,
            is_interface=False,
            description=description,
            directives=directives,
        )

        model._strawberry_type = cls  # type: ignore
        cls._pydantic_type = model  # type: ignore
        return cls

    return wrap
