from decimal import Decimal
from typing import Optional
from uuid import UUID

import pydantic

from .exceptions import UnsupportedTypeError


FIELDS_MAP = {
    pydantic.NoneStr: Optional[str],
    pydantic.NoneBytes: Optional[bytes],
    pydantic.StrBytes: None,
    pydantic.NoneStrBytes: None,
    pydantic.StrictStr: str,
    pydantic.ConstrainedBytes: bytes,
    pydantic.conbytes: bytes,
    pydantic.ConstrainedList: None,
    pydantic.conlist: None,
    pydantic.ConstrainedSet: None,
    pydantic.conset: None,
    pydantic.ConstrainedStr: str,
    pydantic.constr: str,
    pydantic.EmailStr: str,
    pydantic.PyObject: None,
    pydantic.ConstrainedInt: int,
    pydantic.conint: int,
    pydantic.PositiveInt: int,
    pydantic.NegativeInt: int,
    pydantic.ConstrainedFloat: float,
    pydantic.confloat: float,
    pydantic.PositiveFloat: float,
    pydantic.NegativeFloat: float,
    pydantic.ConstrainedDecimal: Decimal,
    pydantic.condecimal: Decimal,
    pydantic.UUID1: UUID,
    pydantic.UUID3: UUID,
    pydantic.UUID4: UUID,
    pydantic.UUID5: UUID,
    pydantic.FilePath: None,
    pydantic.DirectoryPath: None,
    pydantic.Json: None,
    pydantic.JsonWrapper: None,
    pydantic.SecretStr: str,
    pydantic.SecretBytes: bytes,
    pydantic.StrictBool: bool,
    pydantic.StrictInt: int,
    pydantic.StrictFloat: float,
    pydantic.PaymentCardNumber: None,
    pydantic.ByteSize: None,
    pydantic.AnyUrl: str,
    pydantic.AnyHttpUrl: str,
    pydantic.HttpUrl: str,
    pydantic.PostgresDsn: str,
    pydantic.RedisDsn: str,
}


def get_basic_type(type_):
    if isinstance(type_, type):
        if issubclass(type_, pydantic.ConstrainedInt):
            return int
        if issubclass(type_, pydantic.ConstrainedStr):
            return str

    if type_ in FIELDS_MAP:
        type_ = FIELDS_MAP.get(type_)

        if type_ is None:
            raise UnsupportedTypeError()

    return type_
