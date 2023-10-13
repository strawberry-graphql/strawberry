import builtins
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union
from typing_extensions import Annotated
from uuid import UUID

import pydantic
from pydantic import BaseModel

from strawberry.experimental.pydantic._compat import (
    IS_PYDANTIC_V1,
    get_args,
    get_origin,
    is_new_type,
    lenient_issubclass,
    new_type_supertype,
)
from strawberry.experimental.pydantic.exceptions import (
    UnregisteredTypeException,
    UnsupportedTypeError,
)
from strawberry.types.types import StrawberryObjectDefinition

try:
    from types import UnionType as TypingUnionType
except ImportError:
    import sys

    if sys.version_info < (3, 10):
        TypingUnionType = ()
    else:
        raise

try:
    from typing import GenericAlias as TypingGenericAlias  # type: ignore
except ImportError:
    import sys

    # python < 3.9 does not have GenericAlias (list[int], tuple[str, ...] and so on)
    # we do this under a conditional to avoid a mypy :)
    if sys.version_info < (3, 9):
        TypingGenericAlias = ()
    else:
        raise


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
}

ATTR_TO_TYPE_MAP_Pydantic_Core_V2 = {
    "MultiHostUrl": str,
}


def get_fields_map_for_v2() -> Dict[Any, Any]:
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


FIELDS_MAP = (
    {
        getattr(pydantic, field_name): type
        for field_name, type in ATTR_TO_TYPE_MAP.items()
        if hasattr(pydantic, field_name)
    }
    if IS_PYDANTIC_V1
    else get_fields_map_for_v2()
)


def get_basic_type(type_: Any) -> Type[Any]:
    if IS_PYDANTIC_V1:
        # only pydantic v1 has these
        if lenient_issubclass(type_, pydantic.ConstrainedInt):
            return int
        if lenient_issubclass(type_, pydantic.ConstrainedFloat):
            return float
        if lenient_issubclass(type_, pydantic.ConstrainedStr):
            return str
        if lenient_issubclass(type_, pydantic.ConstrainedList):
            return List[get_basic_type(type_.item_type)]  # type: ignore

    if type_ in FIELDS_MAP:
        type_ = FIELDS_MAP.get(type_)
        if type_ is None:
            raise UnsupportedTypeError()

    if is_new_type(type_):
        return new_type_supertype(type_)

    return type_


def replace_pydantic_types(type_: Any, is_input: bool) -> Any:
    if lenient_issubclass(type_, BaseModel):
        attr = "_strawberry_input_type" if is_input else "_strawberry_type"
        if hasattr(type_, attr):
            return getattr(type_, attr)
        else:
            raise UnregisteredTypeException(type_)
    return type_


def replace_types_recursively(type_: Any, is_input: bool) -> Any:
    """Runs the conversions recursively into the arguments of generic types if any"""
    basic_type = get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input)

    origin = get_origin(type_)
    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    converted = tuple(
        replace_types_recursively(t, is_input=is_input) for t in get_args(replaced_type)
    )

    if isinstance(replaced_type, TypingGenericAlias):
        return TypingGenericAlias(origin, converted)
    if isinstance(replaced_type, TypingUnionType):
        return Union[converted]

    # TODO: investigate if we could move the check for annotated to the top
    if origin is Annotated and converted:
        converted = (converted[0],)

    replaced_type = replaced_type.copy_with(converted)

    if isinstance(replaced_type, StrawberryObjectDefinition):
        # TODO: Not sure if this is necessary. No coverage in tests
        # TODO: Unnecessary with StrawberryObject
        replaced_type = builtins.type(
            replaced_type.name,
            (),
            {"__strawberry_definition__": replaced_type},
        )

    return replaced_type
