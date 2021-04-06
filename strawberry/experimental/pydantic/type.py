import dataclasses
from functools import partial
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from pydantic.fields import ModelField

from strawberry.arguments import UNSET
from strawberry.experimental.pydantic.conversion import (
    convert_pydantic_model_to_strawberry_class,
)
from strawberry.experimental.pydantic.fields import get_basic_type
from strawberry.field import StrawberryField
from strawberry.type import _process_type
from strawberry.types.types import FederationTypeParams

from .exceptions import MissingFieldsListError, UnregisteredTypeException


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

        all_fields = [
            (
                name,
                get_type_for_field(field),
                StrawberryField(
                    python_name=field.name,
                    graphql_name=field.alias if field.has_alias else None,
                    default_value=field.default if not field.required else UNSET,
                    default_factory=(
                        field.default_factory if field.default_factory else UNSET
                    ),
                    type_=get_type_for_field(field),
                ),
            )
            for name, field in model_fields.items()
            if name in fields_set
        ]

        cls_annotations = getattr(cls, "__annotations__", {})
        all_fields.extend(
            (
                (
                    name,
                    type_,
                    StrawberryField(
                        python_name=name,
                        graphql_name=None,
                        type_=type_,
                        # we need a default value when adding additional fields
                        # on top of a type generated from Pydantic, this is because
                        # Pydantic Optional fields always have None as default value
                        # which breaks dataclasses generation; as we can't define
                        # a field without a default value after one with a default value
                        # adding fields at the beginning won't work as we will also
                        # support default values on them (so the problem will be just
                        # shifted around)
                        default_value=None,
                    ),
                )
                for name, type_ in cls_annotations.items()
            )
        )

        cls = dataclasses.make_dataclass(
            cls.__name__,
            all_fields,
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

        def from_pydantic(instance: Any, extra: Dict[str, Any] = None) -> Any:
            return convert_pydantic_model_to_strawberry_class(
                cls=cls, model_instance=instance, extra=extra
            )

        def to_pydantic(self) -> Any:
            instance_kwargs = dataclasses.asdict(self)

            return model(**instance_kwargs)

        cls.from_pydantic = staticmethod(from_pydantic)
        cls.to_pydantic = to_pydantic

        return cls

    return wrap


input = partial(type, is_input=True)
