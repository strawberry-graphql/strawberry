import dataclasses
from typing import Any, List, Tuple, Type, Union

from pydantic.typing import NoArgAnyCallable
from pydantic.utils import smart_deepcopy

from strawberry.arguments import _Unset
from strawberry.experimental.pydantic.exceptions import UnregisteredTypeException
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


@dataclasses.dataclass()
class DataclassCreationFields:
    """Fields required for the fields parameter of make_dataclass"""

    name: str
    type_annotation: Any
    field: dataclasses.Field

    @property
    def to_tuple(self) -> Tuple[str, Any, dataclasses.Field]:
        # fields parameter wants (name, type, Field)
        return (self.name, self.type_annotation, self.field)


def sort_creation_fields(
    fields: List[DataclassCreationFields],
) -> List[DataclassCreationFields]:
    """
    Sort fields so that fields with missing defaults go first
    because dataclasses require that fields with no defaults are defined
    first
    """
    missing_default: List[DataclassCreationFields] = []
    has_default: List[DataclassCreationFields] = []
    for model_field in fields:
        if (
            model_field.field.default is dataclasses.MISSING
            and model_field.field.default_factory is dataclasses.MISSING  # type: ignore
        ):
            missing_default.append(model_field)
        else:
            has_default.append(model_field)
    return missing_default + has_default


def defaults_into_factory(
    default: Union[_Unset, Any], default_factory: Union[_Unset, NoArgAnyCallable]
) -> Union[NoArgAnyCallable, _Unset]:
    """
    Handle mutable defaults when making the dataclass by using pydantic's smart_deepcopy
    Returns optionally a NoArgAnyCallable representing a default_factory parameter
    """
    final_factory = default_factory
    if not isinstance(default, _Unset):
        if not isinstance(default_factory, _Unset):
            raise DefaultAndDefaultFactoryDefined(
                default=default, default_factory=default_factory
            )
        else:

            def factory_func():
                return smart_deepcopy(default)

            final_factory = factory_func

    return final_factory
