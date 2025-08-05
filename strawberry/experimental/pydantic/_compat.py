import dataclasses
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Optional
from uuid import UUID

import pydantic
from pydantic import BaseModel
from pydantic.version import VERSION as PYDANTIC_VERSION

from strawberry.experimental.pydantic.exceptions import UnsupportedTypeError

if TYPE_CHECKING:
    from pydantic.fields import ComputedFieldInfo, FieldInfo

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
    is_v1: bool

    @property
    def has_default_factory(self) -> bool:
        return self.default_factory is not self._missing_type

    @property
    def has_default(self) -> bool:
        return self.default is not self._missing_type


ATTR_TO_TYPE_MAP = {
    "NoneStr": Optional[str],
    "NoneBytes": Optional[bytes],
    "StrBytes": None,
    "NoneStrBytes": None,
    "StrictStr": str,
    "ConstrainedBytes": bytes,
    "conbytes": bytes,
    "ConstrainedStr": str,
    "constr": str,
    "EmailStr": str,
    "PyObject": None,
    "ConstrainedInt": int,
    "conint": int,
    "PositiveInt": int,
    "NegativeInt": int,
    "ConstrainedFloat": float,
    "confloat": float,
    "PositiveFloat": float,
    "NegativeFloat": float,
    "ConstrainedDecimal": Decimal,
    "condecimal": Decimal,
    "UUID1": UUID,
    "UUID3": UUID,
    "UUID4": UUID,
    "UUID5": UUID,
    "FilePath": None,
    "DirectoryPath": None,
    "Json": None,
    "JsonWrapper": None,
    "SecretStr": str,
    "SecretBytes": bytes,
    "StrictBool": bool,
    "StrictInt": int,
    "StrictFloat": float,
    "PaymentCardNumber": None,
    "ByteSize": None,
    "AnyUrl": str,
    "AnyHttpUrl": str,
    "HttpUrl": str,
    "PostgresDsn": str,
    "RedisDsn": str,
}

ATTR_TO_TYPE_MAP_Pydantic_V2 = {
    "EmailStr": str,
    "SecretStr": str,
    "SecretBytes": bytes,
    "AnyUrl": str,
    "AnyHttpUrl": str,
    "HttpUrl": str,
    "PostgresDsn": str,
    "RedisDsn": str,
}

ATTR_TO_TYPE_MAP_Pydantic_Core_V2 = {
    "MultiHostUrl": str,
}


def get_fields_map_for_v2() -> dict[Any, Any]:
    import pydantic_core

    fields_map = {
        getattr(pydantic, field_name): type
        for field_name, type in ATTR_TO_TYPE_MAP_Pydantic_V2.items()
        if hasattr(pydantic, field_name)
    }
    fields_map.update(
        {
            getattr(pydantic_core, field_name): type
            for field_name, type in ATTR_TO_TYPE_MAP_Pydantic_Core_V2.items()
            if hasattr(pydantic_core, field_name)
        }
    )

    return fields_map


class PydanticV2Compat:
    @property
    def PYDANTIC_MISSING_TYPE(self) -> Any:  # noqa: N802
        from pydantic_core import PydanticUndefined

        return PydanticUndefined

    def get_model_computed_fields(
        self, model: type[BaseModel]
    ) -> dict[str, CompatModelField]:
        computed_field_info: dict[str, ComputedFieldInfo] = model.model_computed_fields
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in computed_field_info.items():
            new_fields[name] = CompatModelField(
                name=name,
                type_=field.return_type,
                outer_type_=field.return_type,
                default=None,
                default_factory=None,
                required=False,
                alias=field.alias,
                # v2 doesn't have allow_none
                allow_none=False,
                has_alias=field is not None,
                description=field.description,
                _missing_type=self.PYDANTIC_MISSING_TYPE,
                is_v1=False,
            )
        return new_fields

    def get_model_fields(
        self, model: type[BaseModel], include_computed: bool = False
    ) -> dict[str, CompatModelField]:
        field_info: dict[str, FieldInfo] = model.model_fields
        new_fields = {}
        # Convert it into CompatModelField
        for name, field in field_info.items():
            new_fields[name] = CompatModelField(
                name=name,
                type_=field.annotation,
                outer_type_=field.annotation,
                default=field.default,
                default_factory=field.default_factory,  # type: ignore
                required=field.is_required(),
                alias=field.alias,
                # v2 doesn't have allow_none
                allow_none=False,
                has_alias=field is not None,
                description=field.description,
                _missing_type=self.PYDANTIC_MISSING_TYPE,
                is_v1=False,
            )
        if include_computed:
            new_fields |= self.get_model_computed_fields(model)
        return new_fields

    @cached_property
    def fields_map(self) -> dict[Any, Any]:
        return get_fields_map_for_v2()

    def get_basic_type(self, type_: Any) -> type[Any]:
        if type_ in self.fields_map:
            type_ = self.fields_map[type_]

            if type_ is None:
                raise UnsupportedTypeError

        if is_new_type(type_):
            return new_type_supertype(type_)

        return type_

    def model_dump(self, model_instance: BaseModel) -> dict[Any, Any]:
        return model_instance.model_dump()


class PydanticV1Compat:
    @property
    def PYDANTIC_MISSING_TYPE(self) -> Any:  # noqa: N802
        return dataclasses.MISSING

    def get_model_fields(
        self, model: type[BaseModel], include_computed: bool = False
    ) -> dict[str, CompatModelField]:
        """`include_computed` is a noop for PydanticV1Compat."""
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
                is_v1=True,
            )
        return new_fields

    @cached_property
    def fields_map(self) -> dict[Any, Any]:
        if IS_PYDANTIC_V2:
            return {
                getattr(pydantic.v1, field_name): type
                for field_name, type in ATTR_TO_TYPE_MAP.items()
                if hasattr(pydantic.v1, field_name)
            }

        return {
            getattr(pydantic, field_name): type
            for field_name, type in ATTR_TO_TYPE_MAP.items()
            if hasattr(pydantic, field_name)
        }

    def get_basic_type(self, type_: Any) -> type[Any]:
        if IS_PYDANTIC_V1:
            ConstrainedInt = pydantic.ConstrainedInt
            ConstrainedFloat = pydantic.ConstrainedFloat
            ConstrainedStr = pydantic.ConstrainedStr
            ConstrainedList = pydantic.ConstrainedList
        else:
            ConstrainedInt = pydantic.v1.ConstrainedInt
            ConstrainedFloat = pydantic.v1.ConstrainedFloat
            ConstrainedStr = pydantic.v1.ConstrainedStr
            ConstrainedList = pydantic.v1.ConstrainedList

        if lenient_issubclass(type_, ConstrainedInt):  # type: ignore
            return int
        if lenient_issubclass(type_, ConstrainedFloat):  # type: ignore
            return float
        if lenient_issubclass(type_, ConstrainedStr):  # type: ignore
            return str
        if lenient_issubclass(type_, ConstrainedList):  # type: ignore
            return list[self.get_basic_type(type_.item_type)]  # type: ignore

        if type_ in self.fields_map:
            type_ = self.fields_map[type_]

            if type_ is None:
                raise UnsupportedTypeError

        if is_new_type(type_):
            return new_type_supertype(type_)

        return type_

    def model_dump(self, model_instance: BaseModel) -> dict[Any, Any]:
        return model_instance.dict()


class PydanticCompat:
    def __init__(self, is_v2: bool) -> None:
        if is_v2:
            self._compat = PydanticV2Compat()
        else:
            self._compat = PydanticV1Compat()  # type: ignore[assignment]

    @classmethod
    def from_model(cls, model: type[BaseModel]) -> "PydanticCompat":
        if hasattr(model, "model_fields"):
            return cls(is_v2=True)

        return cls(is_v2=False)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._compat, name)


if IS_PYDANTIC_V2:
    from typing_extensions import get_args, get_origin

    from pydantic.v1.typing import is_new_type
    from pydantic.v1.utils import lenient_issubclass, smart_deepcopy

    def new_type_supertype(type_: Any) -> Any:
        return type_.__supertype__
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

__all__ = [
    "PydanticCompat",
    "get_args",
    "get_origin",
    "is_new_type",
    "lenient_issubclass",
    "new_type_supertype",
    "smart_deepcopy",
]
