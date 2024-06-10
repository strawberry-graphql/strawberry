from __future__ import annotations

from abc import abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Type, Union
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
    async def subscribe(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> Any:
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

    @staticmethod
    def remove_field_suggestion(error: GraphQLError) -> None:
        if (
            error.message.startswith("Cannot query field")
            and "Did you mean" in error.message
        ):
            error.message = error.message.split("Did you mean")[0].strip()

    def _process_errors(
        self,
        errors: List[GraphQLError],
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        if self.config.disable_field_suggestions:
            for error in errors:
                self.remove_field_suggestion(error)

        self.process_errors(errors, execution_context)

    def process_errors(
        self,
        errors: List[GraphQLError],
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        for error in errors:
            StrawberryLogger.error(error, execution_context)
