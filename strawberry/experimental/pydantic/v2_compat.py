from dataclasses import dataclass
from typing import Dict, Type, Any, Optional, Callable

import pydantic
from pydantic import BaseModel
from pydantic.v1.typing import NoArgAnyCallable
from pydantic.version import VERSION as PYDANTIC_VERSION

IS_PYDANTIC_V2: bool = PYDANTIC_VERSION.startswith("2.")


@dataclass
class CompatModelField:
    name: str
    outer_type_: Any
    default: Any
    default_factory: Optional[Callable[[], Any]]
    required: bool
    alias: str
    allow_none: bool
    has_alias: bool
    description: str


if pydantic.VERSION[0] == "2":
    from pydantic._internal._utils import smart_deepcopy
    from pydantic._internal._utils import lenient_issubclass
    from typing_extensions import get_args, get_origin
    from pydantic._internal._typing_extra import is_new_type
    from pydantic.v1.fields import ModelField
    from pydantic.fields import FieldInfo

    def new_type_supertype(type_):
        return type_.__supertype__

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, CompatModelField]:
        field_info: dict[str, FieldInfo] = model.model_fields
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in field_info.items():
            new_fields[name] = CompatModelField(
                name=name,
                outer_type_=field.annotation,
                default=field.default,
                default_factory=field.default_factory,
                required=field.is_required(),
                alias=field.alias,
                # v2 doesn't have allow_none
                allow_none=False,
                has_alias=field is not None,
                description=field.description,
            )
        return new_fields

else:
    from pydantic.utils import smart_deepcopy
    from pydantic.utils import lenient_issubclass
    from pydantic.typing import get_args, get_origin, is_new_type, new_type_supertype
    from pydantic import ModelField

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, CompatModelField]:
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in model.__fields__.items():
            new_fields[name] = CompatModelField(
                name=name,
                outer_type_=field.type_,
                default=field.default,
                default_factory=field.default_factory,
                required=field.required,
                alias=field.alias,
                allow_none=field.allow_none,
                has_alias=field.has_alias,
                description=field.field_info.description,
            )
        return new_fields


__all__ = ["smart_deepcopy", "lenient_issubclass"]
