from __future__ import annotations

from abc import abstractmethod
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)
from typing_extensions import Protocol

from strawberry.utils.logging import StrawberryLogger

if TYPE_CHECKING:
    from graphql import GraphQLError

    from strawberry.custom_scalar import ScalarDefinition
    from strawberry.directive import StrawberryDirective
    from strawberry.enum import EnumDefinition
    from strawberry.schema.schema_converter import GraphQLCoreConverter
    from strawberry.types import ExecutionContext, ExecutionResult
    from strawberry.types.graphql import OperationType
    from strawberry.types.types import StrawberryObjectDefinition
    from strawberry.union import StrawberryUnion

    from .config import StrawberryConfig


class SubscribeSingleResult(RuntimeError):
    """Raised when Schema.subscribe() returns a single execution result, instead of a
    subscription generator, typically as a result of validation errors.
    """

    def __init__(self, value: ExecutionResult) -> None:
        self.value = value


class BaseSchema(Protocol):
    config: StrawberryConfig
    schema_converter: GraphQLCoreConverter
    query: Type
    mutation: Optional[Type]
    subscription: Optional[Type]
    schema_directives: List[object]

    @abstractmethod
    async def execute(
        self,
        query: Optional[str],
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
    ) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    def execute_sync(
        self,
        query: Optional[str],
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
    ) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> AsyncGenerator[ExecutionResult, None]:
        raise NotImplementedError

    @abstractmethod
    def get_type_by_name(
        self, name: str
    ) -> Optional[
        Union[
            StrawberryObjectDefinition,
            ScalarDefinition,
            EnumDefinition,
            StrawberryUnion,
        ]
    ]:
        raise NotImplementedError

    @abstractmethod
    @lru_cache
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
