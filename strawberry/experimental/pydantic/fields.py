from decimal import Decimal
from typing import Any, List, Optional, Type
from uuid import UUID

import pydantic
from pydantic.typing import is_new_type, new_type_supertype

from .exceptions import UnsupportedTypeError


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


FIELDS_MAP = {
    getattr(pydantic, field_name): type
    for field_name, type in ATTR_TO_TYPE_MAP.items()
    if hasattr(pydantic, field_name)
}


def get_basic_type(type_) -> Type[Any]:
    if isinstance(type_, type):
        if issubclass(type_, pydantic.ConstrainedInt):
            return int
        if issubclass(type_, pydantic.ConstrainedStr):
            return str
        if issubclass(type_, pydantic.ConstrainedList):
            return List[get_basic_type(type_.item_type)]  # type: ignore

    if type_ in FIELDS_MAP:
        type_ = FIELDS_MAP.get(type_)

        if type_ is None:
            raise UnsupportedTypeError()

    if is_new_type(type_):
        return new_type_supertype(type_)

    return type_
