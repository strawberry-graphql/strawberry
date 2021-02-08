import dataclasses
from typing import Generic, TypeVar

from graphql import OperationDefinitionNode
from graphql.pyutils.path import Path


ContextType = TypeVar("ContextType")
RootValueType = TypeVar("RootValueType")


@dataclasses.dataclass
class Info(Generic[ContextType, RootValueType]):
    field_name: str
    context: ContextType
    root_value: RootValueType
    # TODO: create an abstraction on these fields
    operation: OperationDefinitionNode
    path: Path
    # TODO: parent_type, return_type as strawberry types
