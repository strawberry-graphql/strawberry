from abc import abstractmethod
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from typing_extensions import Protocol

from graphql import GraphQLError

from strawberry.custom_scalar import ScalarDefinition
from strawberry.directive import StrawberryDirective
from strawberry.enum import EnumDefinition
from strawberry.types import ExecutionContext, ExecutionResult
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.logging import StrawberryLogger

from .config import StrawberryConfig


class BaseSchema(Protocol):
    config: StrawberryConfig

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
    @lru_cache()
    def get_directive_by_name(self, graphql_name: str) -> Optional[StrawberryDirective]:
        raise NotImplementedError

    @abstractmethod
    def as_str(self) -> str:
        raise NotImplementedError

    def process_errors(
        self,
        errors: List[GraphQLError],
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        for error in errors:
            StrawberryLogger.error(error, execution_context)
