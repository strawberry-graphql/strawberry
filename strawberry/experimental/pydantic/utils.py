import dataclasses
from typing import Any, List, NamedTuple, NoReturn, Set, Tuple, Type, Union, cast

from pydantic import BaseModel
from pydantic.fields import ModelField
from pydantic.typing import NoArgAnyCallable
from pydantic.utils import smart_deepcopy

from strawberry.arguments import UNSET, _Unset, is_unset  # type: ignore
from strawberry.experimental.pydantic.exceptions import (
    AutoFieldsNotInBaseModelError,
    BothDefaultAndDefaultFactoryDefinedError,
    UnregisteredTypeException,
)
from strawberry.private import is_private
from strawberry.utils.typing import (
    get_list_annotation,
    get_optional_annotation,
    is_list,
    is_optional,
)


def normalize_type(type_) -> Any:
    if is_list(type_):
        return List[normalize_type(get_list_annotation(type_))]  # type: ignore

    if is_optional(type_):
        return get_optional_annotation(type_)

    return type_


def get_strawberry_type_from_model(type_: Any):
    if hasattr(type_, "_strawberry_type"):
        return type_._strawberry_type
    else:
        raise UnregisteredTypeException(type_)


def get_private_fields(cls: Type) -> List[dataclasses.Field]:
    private_fields: List[dataclasses.Field] = []

    for field in dataclasses.fields(cls):
        if is_private(field.type):
            private_fields.append(field)

    return private_fields


class DataclassCreationFields(NamedTuple):
    """Fields required for the fields parameter of make_dataclass"""

    name: str
    type_annotation: Type
    field: dataclasses.Field

    def to_tuple(self) -> Tuple[str, Type, dataclasses.Field]:
        # fields parameter wants (name, type, Field)
        return self.name, self.type_annotation, self.field


def sort_creation_fields(
    fields: List[DataclassCreationFields],
) -> List[DataclassCreationFields]:
    """
    Sort fields so that fields with missing defaults go first
    because dataclasses require that fields with no defaults are defined
    first
    """

    def has_default(model_field: DataclassCreationFields) -> bool:
        """Check if field has defaults."""
        return (model_field.field.default is not dataclasses.MISSING) or (
            model_field.field.default_factory is not dataclasses.MISSING
        )

    return sorted(fields, key=has_default)


def get_default_factory_for_field(field: ModelField) -> Union[NoArgAnyCallable, _Unset]:
    """
    Gets the default factory for a pydantic field.

    Handles mutable defaults when making the dataclass by using pydantic's smart_deepcopy

    Returns optionally a NoArgAnyCallable representing a default_factory parameter
    """
    default_factory = field.default_factory
    default = field.default

    has_factory = default_factory is not None and not is_unset(default_factory)
    has_default = default is not None and not is_unset(default)

    # defining both default and default_factory is not supported

    if has_factory and has_default:
        default_factory = cast(NoArgAnyCallable, default_factory)

        raise BothDefaultAndDefaultFactoryDefinedError(
            default=default, default_factory=default_factory
        )

    # if we have a default_factory, we should return it

    if has_factory:
        default_factory = cast(NoArgAnyCallable, default_factory)

        return default_factory

    # if we have a default, we should return it

    if has_default:
        return lambda: smart_deepcopy(default)

    # if we don't have default or default_factory, but the field is not required,
    # we should return a factory that returns None

    if not field.required:
        return lambda: None

    return UNSET


def ensure_all_auto_fields_in_pydantic(
    model: Type[BaseModel], auto_fields: Set[str], cls_name: str
) -> Union[NoReturn, None]:
    # Raise error if user defined a strawberry.auto field not present in the model
    non_existing_fields = list(auto_fields - model.__fields__.keys())

    if non_existing_fields:
        raise AutoFieldsNotInBaseModelError(
            fields=non_existing_fields, cls_name=cls_name, model=model
        )
    else:
        return None
