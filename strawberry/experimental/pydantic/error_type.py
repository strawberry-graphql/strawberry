from __future__ import annotations

import dataclasses
import warnings
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from pydantic import BaseModel

from strawberry.experimental.pydantic._compat import (
    CompatModelField,
    PydanticCompat,
    lenient_issubclass,
)
from strawberry.experimental.pydantic.utils import (
    get_private_fields,
    get_strawberry_type_from_model,
    normalize_type,
)
from strawberry.types.auto import StrawberryAuto
from strawberry.types.object_type import _process_type, _wrap_dataclass
from strawberry.types.type_resolver import _get_fields
from strawberry.utils.typing import get_list_annotation, is_list

from .exceptions import MissingFieldsListError


def get_type_for_field(field: CompatModelField) -> Union[Any, Type[None], Type[List]]:
    type_ = field.outer_type_
    type_ = normalize_type(type_)
    return field_type_to_type(type_)


def field_type_to_type(type_: Type) -> Union[Any, List[Any], None]:
    error_class: Any = str
    strawberry_type: Any = error_class

    if is_list(type_):
        child_type = get_list_annotation(type_)

        if is_list(child_type):
            strawberry_type = field_type_to_type(child_type)
        elif lenient_issubclass(child_type, BaseModel):
            strawberry_type = get_strawberry_type_from_model(child_type)
        else:
            strawberry_type = List[error_class]

        strawberry_type = Optional[strawberry_type]
    elif lenient_issubclass(type_, BaseModel):
        strawberry_type = get_strawberry_type_from_model(type_)
        return Optional[strawberry_type]

    return Optional[List[strawberry_type]]


def error_type(
    model: Type[BaseModel],
    *,
    fields: Optional[List[str]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    all_fields: bool = False,
) -> Callable[..., Type]:
    def wrap(cls: Type) -> Type:
        compat = PydanticCompat.from_model(model)
        model_fields = compat.get_model_fields(model)
        fields_set = set(fields) if fields else set()

        if fields:
            warnings.warn(
                "`fields` is deprecated, use `auto` type annotations instead",
                DeprecationWarning,
                stacklevel=2,
            )

        existing_fields = getattr(cls, "__annotations__", {})
        auto_fields_set = {
            name
            for name, type_ in existing_fields.items()
            if isinstance(type_, StrawberryAuto)
        }
        fields_set |= auto_fields_set

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
                dataclasses.field(default=None),  # type: ignore[arg-type]
            )
            for name, field in model_fields.items()
            if name in fields_set
        ]

        wrapped = _wrap_dataclass(cls)
        extra_fields = cast(List[dataclasses.Field], _get_fields(wrapped, {}))
        private_fields = get_private_fields(wrapped)

        all_model_fields.extend(
            (
                field.name,
                field.type,
                field,
            )
            for field in extra_fields + private_fields
            if (
                field.name not in auto_fields_set
                and not isinstance(field.type, StrawberryAuto)
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

        model._strawberry_type = cls  # type: ignore[attr-defined]
        cls._pydantic_type = model
        return cls

    return wrap
