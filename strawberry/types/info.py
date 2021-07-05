import dataclasses
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from graphql import OperationDefinitionNode
from graphql.language import FieldNode
from graphql.pyutils.path import Path

from strawberry.union import StrawberryUnion


ContextType = TypeVar("ContextType")
RootValueType = TypeVar("RootValueType")


@dataclasses.dataclass
class Info(Generic[ContextType, RootValueType]):
    field_name: str
    field_nodes: List[FieldNode]
    context: ContextType
    root_value: RootValueType
    variable_values: Dict[str, Any]
    # TODO: update to StrawberryType once it's implemented
    return_type: Optional[Union[Type, StrawberryUnion]]
    # TODO: create an abstraction on these fields
    operation: OperationDefinitionNode
    path: Path
    # TODO: parent_type as strawberry types
