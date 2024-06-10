from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    NamedTuple,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

from pydantic import BaseModel

from strawberry.experimental.pydantic._compat import (
    CompatModelField,
    PydanticCompat,
    smart_deepcopy,
)
from strawberry.experimental.pydantic.exceptions import (
    AutoFieldsNotInBaseModelError,
    BothDefaultAndDefaultFactoryDefinedError,
    UnregisteredTypeException,
)
from strawberry.private import is_private
from strawberry.unset import UNSET
from strawberry.utils.typing import (
    get_list_annotation,
    get_optional_annotation,
    is_list,
    is_optional,
)

if TYPE_CHECKING:
    from pydantic.typing import NoArgAnyCallable


def normalize_type(type_: Type) -> Any:
    if is_list(type_):
        return List[normalize_type(get_list_annotation(type_))]  # type: ignore

    if is_optional(type_):
        return get_optional_annotation(type_)

    return type_


def get_strawberry_type_from_model(type_: Any) -> Any:
    if hasattr(type_, "_strawberry_type"):
        return type_._strawberry_type
    else:
        raise UnregisteredTypeException(type_)


def get_private_fields(cls: Type) -> List[dataclasses.Field]:
    return [field for field in dataclasses.fields(cls) if is_private(field.type)]


class DataclassCreationFields(NamedTuple):
    """Fields required for the fields parameter of make_dataclass"""

    name: str
    field_type: Type
    field: dataclasses.Field

    def to_tuple(self) -> Tuple[str, Type, dataclasses.Field]:
        # fields parameter wants (name, type, Field)
        return self.name, self.field_type, self.field


def get_default_factory_for_field(
    field: CompatModelField,
    compat: PydanticCompat,
) -> Union[NoArgAnyCallable, dataclasses._MISSING_TYPE]:
    """
    Gets the default factory for a pydantic field.

    Handles mutable defaults when making the dataclass by
    using pydantic's smart_deepcopy

    Returns optionally a NoArgAnyCallable representing a default_factory parameter
    """
    # replace dataclasses.MISSING with our own UNSET to make comparisons easier
    default_factory = field.default_factory if field.has_default_factory else UNSET
    default = field.default if field.has_default else UNSET

    has_factory = default_factory is not None and default_factory is not UNSET
    has_default = default is not None and default is not UNSET

    # defining both default and default_factory is not supported

    if has_factory and has_default:
        default_factory = cast("NoArgAnyCallable", default_factory)

        raise BothDefaultAndDefaultFactoryDefinedError(
            default=default, default_factory=default_factory
        )

    # if we have a default_factory, we should return it

    if has_factory:
        default_factory = cast("NoArgAnyCallable", default_factory)

        return default_factory

    # if we have a default, we should return it
    if has_default:
        # if the default value is a pydantic base model
        # we should return the serialized version of that default for
        # printing the value.
        if isinstance(default, BaseModel):
            return lambda: compat.model_dump(default)
        else:
            return lambda: smart_deepcopy(default)

    # if we don't have default or default_factory, but the field is not required,
    # we should return a factory that returns None

    if not field.required:
        return lambda: None

    return dataclasses.MISSING


def ensure_all_auto_fields_in_pydantic(
    model: Type[BaseModel], auto_fields: Set[str], cls_name: str
) -> None:
    compat = PydanticCompat.from_model(model)
    # Raise error if user defined a strawberry.auto field not present in the model
    non_existing_fields = list(auto_fields - compat.get_model_fields(model).keys())

    if non_existing_fields:
        raise AutoFieldsNotInBaseModelError(
            fields=non_existing_fields, cls_name=cls_name, model=model
        )
    else:
        return
