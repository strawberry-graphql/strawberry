import dataclasses
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from typing_extensions import Protocol

from graphql.error.graphql_error import GraphQLError

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None


class BaseSchema(Protocol):
    @abstractmethod
    async def execute(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    def execute_sync(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def get_type_by_name(
        self, name: str
    ) -> Optional[
        Union[TypeDefinition, ScalarDefinition, EnumDefinition, StrawberryUnion]
    ]:
        raise NotImplementedError

    @abstractmethod
    def as_str(self) -> str:
        raise NotImplementedError
