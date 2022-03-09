import dataclasses
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from backports.cached_property import cached_property

from graphql import GraphQLResolveInfo, OperationDefinitionNode
from graphql.language import FieldNode
from graphql.pyutils.path import Path

from strawberry.type import StrawberryType


if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.schema import Schema

from .nodes import Selection, convert_selections


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
    def schema(self) -> "Schema":
        return self._raw_info.schema._strawberry_schema  # type: ignore

    @property
    def field_nodes(self) -> List[FieldNode]:  # deprecated
        warnings.warn(
            "`info.field_nodes` is deprecated, use `selected_fields` instead",
            DeprecationWarning,
        )
        # TODO: remove cast when GraphQL-core > 3.2.0 is release
        return cast(List[FieldNode], self._raw_info.field_nodes)

    @cached_property
    def selected_fields(self) -> List[Selection]:
        info = self._raw_info
        return convert_selections(info, info.field_nodes)

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

    @property
    def python_name(self) -> str:
        return self._field.python_name

    # TODO: create an abstraction on these fields
    @property
    def operation(self) -> OperationDefinitionNode:
        return self._raw_info.operation

    @property
    def path(self) -> Path:
        return self._raw_info.path

    # TODO: parent_type as strawberry types
