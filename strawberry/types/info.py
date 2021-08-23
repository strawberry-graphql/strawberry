import dataclasses
import warnings
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, TypeVar, Union

from graphql import GraphQLResolveInfo, OperationDefinitionNode
from graphql.language import FieldNode
from graphql.pyutils.path import Path

from strawberry.type import StrawberryType


if TYPE_CHECKING:
    from strawberry.field import StrawberryField

from .nodes import SelectedField


ContextType = TypeVar("ContextType")
RootValueType = TypeVar("RootValueType")


@dataclasses.dataclass
class Info(Generic[ContextType, RootValueType]):
    _raw_info: GraphQLResolveInfo
    _field: "StrawberryField"

    @property
    def field_name(self) -> str:
        return self._raw_info.field_name

    @property
    def field_nodes(self) -> List[FieldNode]:  # deprecated
        warnings.warn(
            "`info.field_nodes` is deprecated, use `selected_fields` instead",
            DeprecationWarning,
        )
        return self._raw_info.field_nodes

    @property
    def selected_fields(self) -> List[SelectedField]:
        info = self._raw_info
        return list(map(SelectedField, info.field_nodes))

    @property
    def context(self) -> ContextType:
        return self._raw_info.context

    @property
    def root_value(self) -> RootValueType:
        return self._raw_info.root_value

    @property
    def variable_values(self) -> Dict[str, Any]:
        return self._raw_info.variable_values

    # TODO: merge type with StrawberryType when StrawberryObject is implemented
    @property
    def return_type(self) -> Optional[Union[type, StrawberryType]]:
        return self._field.type

    # TODO: create an abstraction on these fields
    @property
    def operation(self) -> OperationDefinitionNode:
        return self._raw_info.operation

    @property
    def path(self) -> Path:
        return self._raw_info.path

    # TODO: parent_type as strawberry types
