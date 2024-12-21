from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    runtime_checkable,
)
from typing_extensions import Protocol, TypedDict

from graphql import specified_rules

from strawberry.utils.operation import get_first_operation, get_operation_type

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing_extensions import NotRequired

    from graphql import ASTValidationRule
    from graphql import ExecutionResult as GraphQLExecutionResult
    from graphql.error.graphql_error import GraphQLError
    from graphql.language import DocumentNode, OperationDefinitionNode

    from strawberry.schema import Schema

    from .graphql import OperationType


@dataclasses.dataclass
class ExecutionContext:
    query: Optional[str]
    schema: Schema
    allowed_operations: Iterable[OperationType]
    context: Any = None
    variables: Optional[dict[str, Any]] = None
    parse_options: ParseOptions = dataclasses.field(
        default_factory=lambda: ParseOptions()
    )
    root_value: Optional[Any] = None
    validation_rules: tuple[type[ASTValidationRule], ...] = dataclasses.field(
        default_factory=lambda: tuple(specified_rules)
    )

    # The operation name that is provided by the request
    provided_operation_name: dataclasses.InitVar[Optional[str]] = None

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: Optional[DocumentNode] = None
    errors: Optional[list[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None
    extensions_results: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self, provided_operation_name: str | None) -> None:
        self._provided_operation_name = provided_operation_name

    @property
    def operation_name(self) -> Optional[str]:
        if self._provided_operation_name:
            return self._provided_operation_name

        definition = self._get_first_operation()
        if not definition:
            return None

        if not definition.name:
            return None

        return definition.name.value

    @property
    def operation_type(self) -> OperationType:
        graphql_document = self.graphql_document
        if not graphql_document:
            raise RuntimeError("No GraphQL document available")

        return get_operation_type(graphql_document, self.operation_name)

    def _get_first_operation(self) -> Optional[OperationDefinitionNode]:
        graphql_document = self.graphql_document
        if not graphql_document:
            return None

        return get_first_operation(graphql_document)


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[dict[str, Any]]
    errors: Optional[list[GraphQLError]]
    extensions: Optional[dict[str, Any]] = None


@dataclasses.dataclass
class PreExecutionError(ExecutionResult):
    """Differentiate between a normal execution result and an immediate error.

    Immediate errors are errors that occur before the execution phase i.e validation errors,
    or any other error that occur before we interact with resolvers.

    These errors are required by `graphql-ws-transport` protocol in order to close the operation
    right away once the error is encountered.
    """


class ParseOptions(TypedDict):
    max_tokens: NotRequired[int]


@runtime_checkable
class SubscriptionExecutionResult(Protocol):
    def __aiter__(self) -> SubscriptionExecutionResult:  # pragma: no cover
        ...

    async def __anext__(self) -> Any:  # pragma: no cover
        ...


__all__ = [
    "ExecutionContext",
    "ExecutionResult",
    "ParseOptions",
    "SubscriptionExecutionResult",
]
