import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type

from pydantic import BaseModel
from pydantic.version import VERSION as PYDANTIC_VERSION

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

IS_PYDANTIC_V2: bool = PYDANTIC_VERSION.startswith("2.")
IS_PYDANTIC_V1: bool = not IS_PYDANTIC_V2


@dataclass
class CompatModelField:
    name: str
    type_: Any
    outer_type_: Any
    default: Any
    default_factory: Optional[Callable[[], Any]]
    required: bool
    alias: Optional[str]
    allow_none: bool
    has_alias: bool
    description: Optional[str]


if IS_PYDANTIC_V2:
    from typing_extensions import get_args, get_origin

    from pydantic._internal._typing_extra import is_new_type
    from pydantic._internal._utils import lenient_issubclass, smart_deepcopy
    from pydantic_core import PydanticUndefined

    PYDANTIC_MISSING_TYPE = PydanticUndefined

    def new_type_supertype(type_: Any) -> Any:
        return type_.__supertype__

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, CompatModelField]:
        field_info: dict[str, FieldInfo] = model.model_fields
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in field_info.items():
            new_fields[name] = CompatModelField(
                name=name,
                type_=field.annotation,
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
    from pydantic.typing import (  # type: ignore[no-redef]
        get_args,
        get_origin,
        is_new_type,
        new_type_supertype,
    )
    from pydantic.utils import (  # type: ignore[no-redef]
        lenient_issubclass,
        smart_deepcopy,
    )

    PYDANTIC_MISSING_TYPE = dataclasses.MISSING  # type: ignore[assignment]

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, CompatModelField]:
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in model.__fields__.items():  # type: ignore[attr-defined]
            new_fields[name] = CompatModelField(
                name=name,
                type_=field.type_,
                outer_type_=field.outer_type_,
                default=field.default,
                default_factory=field.default_factory,
                required=field.required,
                alias=field.alias,
                allow_none=field.allow_none,
                has_alias=field.has_alias,
                description=field.field_info.description,
            )
        return new_fields


__all__ = [
    "smart_deepcopy",
    "lenient_issubclass",
    "get_args",
    "get_origin",
    "is_new_type",
    "new_type_supertype",
    "get_model_fields",
    "PYDANTIC_MISSING_TYPE",
]
