import dataclasses
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from graphql import OperationDefinitionNode
from graphql.language import FieldNode
from graphql.pyutils.path import Path

from strawberry.type import StrawberryType

from .nodes import SelectedField


ContextType = TypeVar("ContextType")
RootValueType = TypeVar("RootValueType")


@dataclasses.dataclass
class Info(Generic[ContextType, RootValueType]):
    field_name: str
    field_nodes: List[FieldNode]  # deprecated
    selected_fields: List[SelectedField]
    context: ContextType
    root_value: RootValueType
    variable_values: Dict[str, Any]
    # TODO: merge type with StrawberryType when StrawberryObject is implemented
    return_type: Optional[Union[type, StrawberryType]]
    # TODO: create an abstraction on these fields
    operation: OperationDefinitionNode
    path: Path
    # TODO: parent_type as strawberry types
