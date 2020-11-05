import dataclasses
from functools import partial
from typing import Any, List, Optional, Type

from pydantic import BaseModel
from pydantic.fields import ModelField

from strawberry.beta.pydantic.fields import get_basic_type
from strawberry.beta.pydantic.utils import (
    get_strawberry_type_from_model,
    normalize_type,
)
from strawberry.type import _process_type
from strawberry.types.types import FederationTypeParams
from strawberry.utils.typing import get_list_annotation, is_list

from .exceptions import MissingFieldsListError, UnregisteredTypeException


def parse_type_to_data(type_, data):
    if is_list(type_):
        inner_type = get_list_annotation(type_)
        items = [None for _ in data]

        if is_list(inner_type):
            for index, item in enumerate(data):
                items[index] = parse_type_to_data(inner_type, item)

            return items
        elif issubclass(inner_type, BaseModel):
            # The inner type is a model so we take the
            # strawberry type and convert it
            strawberry_type = get_strawberry_type_from_model(inner_type)

            for index, item in enumerate(data):
                items[index] = convert_class(item, strawberry_type)
        else:
            # We do not know how to better convert the data
            # so we just put the raw value
            for index, item in enumerate(data):
                items[index] = item

        return items
    elif issubclass(type_, BaseModel):
        strawberry_type = get_strawberry_type_from_model(type_)
        return strawberry_type.from_pydantic(data)
    else:
        return data


def convert_class(model_instance, cls):
    kwargs = {}

    for name, field in model_instance.__fields__.items():
        outer_type = normalize_type(field.outer_type_)
        data = getattr(model_instance, name)
        kwargs[name] = parse_type_to_data(outer_type, data)

    return cls(**kwargs)


def replace_pydantic_types(type_: Any):
    if hasattr(type_, "__args__"):
        return type_.copy_with(tuple(replace_pydantic_types(t) for t in type_.__args__))

    if issubclass(type_, BaseModel):
        if hasattr(type_, "_strawberry_type"):
            return type_._strawberry_type
        else:
            raise UnregisteredTypeException(type_)

    return type_


def get_type_for_field(field: ModelField):
    type_ = field.outer_type_
    type_ = get_basic_type(type_)
    type_ = replace_pydantic_types(type_)

    if not field.required:
        type_ = Optional[type_]

    return type_


def type(
    model: Type[BaseModel],
    *,
    fields: List[str],
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    federation: Optional[FederationTypeParams] = None,
):
    def wrap(cls):
        if not fields:
            raise MissingFieldsListError(model)

        model_fields = model.__fields__
        fields_set = set(fields)

        cls = dataclasses.make_dataclass(
            cls.__name__,
            [
                (name, get_type_for_field(field))
                for name, field in model_fields.items()
                if name in fields_set
            ],
        )

        _process_type(
            cls,
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            description=description,
            federation=federation,
        )

        model._strawberry_type = cls  # type: ignore

        def from_pydantic(instance: Any, **kwargs) -> Any:
            return convert_class(model_instance=instance, cls=cls)

        def to_pydantic(self) -> Any:
            instance_kwargs = dataclasses.asdict(self)

            return model(**instance_kwargs)

        cls.from_pydantic = staticmethod(from_pydantic)
        cls.to_pydantic = to_pydantic

        return cls

    return wrap


input = partial(type, is_input=True)
