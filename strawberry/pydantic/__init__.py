import dataclasses
from typing import Any, Optional, Type, cast

from pydantic import BaseModel
from pydantic.fields import ModelField
from strawberry.type import _process_type
from strawberry.types.types import FederationTypeParams


class UnregisteredTypeException(Exception):
    def __init__(self, type: BaseModel):
        message = (
            f"Cannot find a Strawberry Type for {type} did you forget to register it?"
        )

        super().__init__(message)


def resolve_type(field: ModelField) -> Type:
    field_type = {str: str, int: int}.get(field.type_)

    if field_type is None:
        if issubclass(field.type_, BaseModel):
            if hasattr(field.type_, "_strawberry_type"):
                return field.type_._strawberry_type

            raise UnregisteredTypeException(field.type_)

    return cast(Type, field_type)


def get_type_for_field(field: ModelField):
    type_ = field.type_

    if issubclass(type_, BaseModel):
        if hasattr(type_, "_strawberry_type"):
            type_ = type_._strawberry_type
        else:
            raise UnregisteredTypeException(type_)

    if not field.required:
        return Optional[type_]

    return type_


def type(
    model: Type[BaseModel],
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    federation: Optional[FederationTypeParams] = None,
):
    def wrap(cls):
        fields = model.__fields__

        cls = dataclasses.make_dataclass(
            cls.__name__,
            [(name, get_type_for_field(field)) for name, field in fields.items()],
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

        def from_pydantic(instance: Any, **kwargs) -> model:
            instance_kwargs = instance.dict()

            # TODO: convert nested data

            return model(**{**instance_kwargs, **kwargs})

        cls.from_pydantic = staticmethod(from_pydantic)

        return cls

    return wrap
