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
    _missing_type: Any

    @property
    def has_default_factory(self) -> bool:
        return self.default_factory is not self._missing_type

    @property
    def has_default(self) -> bool:
        return self.default is not self._missing_type


class PydanticV2Compat:
    def new_type_supertype(self, type_: Any) -> Any:
        return type_.__supertype__

    @property
    def PYDANTIC_MISSING_TYPE(self) -> Any:
        from pydantic_core import PydanticUndefined

        return PydanticUndefined

    def get_model_fields(self, model: Type[BaseModel]) -> Dict[str, CompatModelField]:
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
                _missing_type=self.PYDANTIC_MISSING_TYPE,
            )
        return new_fields


class PydanticV1Compat:
    @property
    def PYDANTIC_MISSING_TYPE(self) -> Any:
        return dataclasses.MISSING

    def get_model_fields(self, model: Type[BaseModel]) -> Dict[str, CompatModelField]:
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
                _missing_type=self.PYDANTIC_MISSING_TYPE,
            )
        return new_fields

    def new_type_supertype(self, type_: Any) -> Any:
        return type_


class PydanticCompat:
    # proxy based on v1 or v2
    def __init__(self):
        if IS_PYDANTIC_V2:
            self._compat = PydanticV2Compat()
        else:
            self._compat = PydanticV1Compat()

    @classmethod
    def from_model(cls, model: Type[BaseModel]) -> "PydanticCompat":
        return cls()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._compat, name)


if IS_PYDANTIC_V2:
    from typing_extensions import get_args, get_origin

    from pydantic._internal._typing_extra import is_new_type
    from pydantic._internal._utils import lenient_issubclass, smart_deepcopy

    def new_type_supertype(type_: Any) -> Any:
        return type_.__supertype__
else:
    from pydantic.typing import get_args, get_origin, is_new_type
    from pydantic.utils import lenient_issubclass, smart_deepcopy


__all__ = [
    "PydanticCompat",
    "is_new_type",
    "lenient_issubclass",
    "get_origin",
    "get_args",
    "new_type_supertype",
    "smart_deepcopy",
]
