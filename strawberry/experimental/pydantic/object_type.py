import builtins
import dataclasses
from functools import partial
from typing import Any, Dict, List, Optional, Tuple, Type, cast

from pydantic import BaseModel
from pydantic.fields import ModelField

from strawberry.arguments import UNSET
from strawberry.experimental.pydantic.conversion import (
    convert_pydantic_model_to_strawberry_class,
)
from strawberry.experimental.pydantic.fields import get_basic_type
from strawberry.field import StrawberryField
from strawberry.object_type import _process_type, _wrap_dataclass
from strawberry.private import Private
from strawberry.types.type_resolver import _get_fields
from strawberry.types.types import FederationTypeParams, TypeDefinition

from .exceptions import MissingFieldsListError, UnregisteredTypeException


def replace_pydantic_types(type_: Any):
    if hasattr(type_, "__args__"):
        new_type = type_.copy_with(
            tuple(replace_pydantic_types(t) for t in type_.__args__)
        )

        if isinstance(new_type, TypeDefinition):
            # TODO: Not sure if this is necessary. No coverage in tests
            # TODO: Unnecessary with StrawberryObject

            new_type = builtins.type(
                new_type.name,
                (),
                {"_type_definition": new_type},
            )

        return new_type

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


def _get_private_fields(cls: Type) -> List[dataclasses.Field]:
    private_fields: List[dataclasses.Field] = []
    for field in dataclasses.fields(cls):
        if isinstance(field.type, Private):
            private_fields.append(field)
    return private_fields


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

        all_fields: List[Tuple[str, Any, dataclasses.Field]] = [
            (
                name,
                get_type_for_field(field),
                StrawberryField(
                    python_name=field.name,
                    graphql_name=field.alias if field.has_alias else None,
                    default=field.default if not field.required else UNSET,
                    default_factory=(
                        field.default_factory if field.default_factory else UNSET
                    ),
                    type_annotation=get_type_for_field(field),
                ),
            )
            for name, field in model_fields.items()
            if name in fields_set
        ]

        wrapped = _wrap_dataclass(cls)
        extra_fields = cast(List[dataclasses.Field], _get_fields(wrapped))
        private_fields = _get_private_fields(wrapped)

        all_fields.extend(
            (
                (
                    field.name,
                    field.type,
                    field,
                )
                for field in extra_fields + private_fields
            )
        )

        # Sort fields so that fields with missing defaults go first
        # because dataclasses require that fields with no defaults are defined
        # first
        missing_default = []
        has_default = []
        for field in all_fields:
            if field[2].default is dataclasses.MISSING:
                missing_default.append(field)
            else:
                has_default.append(field)

        sorted_fields = missing_default + has_default

        cls = dataclasses.make_dataclass(
            cls.__name__,
            sorted_fields,
            bases=cls.__bases__,
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
        cls._pydantic_type = model  # type: ignore

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

interface = partial(type, is_interface=True)
