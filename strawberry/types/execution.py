from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    runtime_checkable,
)
from typing_extensions import Protocol, TypedDict, deprecated

from graphql import specified_rules

from strawberry.utils.operation import get_first_operation, get_operation_type

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing_extensions import NotRequired

    from graphql import ASTValidationRule
    from graphql.error.graphql_error import GraphQLError
    from graphql.language import DocumentNode, OperationDefinitionNode

    from strawberry.schema import Schema
    from strawberry.schema._graphql_core import GraphQLExecutionResult

    from .graphql import OperationType


@dataclasses.dataclass
class ExecutionContext:
    query: str | None
    schema: Schema
    allowed_operations: Iterable[OperationType]
    context: Any = None
    variables: dict[str, Any] | None = None
    parse_options: ParseOptions = dataclasses.field(
        default_factory=lambda: ParseOptions()
    )
    root_value: Any | None = None
    validation_rules: tuple[type[ASTValidationRule], ...] = dataclasses.field(
        default_factory=lambda: tuple(specified_rules)
    )

    # The operation name that is provided by the request
    provided_operation_name: dataclasses.InitVar[str | None] = None

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: DocumentNode | None = None
    pre_execution_errors: list[GraphQLError] | None = None
    result: GraphQLExecutionResult | None = None
    extensions_results: dict[str, Any] = dataclasses.field(default_factory=dict)

    operation_extensions: dict[str, Any] | None = None

    def __post_init__(self, provided_operation_name: str | None) -> None:
        self._provided_operation_name = provided_operation_name

    @property
    def operation_name(self) -> str | None:
        if self._provided_operation_name is not None:
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

    def _get_first_operation(self) -> OperationDefinitionNode | None:
        graphql_document = self.graphql_document
        if not graphql_document:
            return None

        return get_first_operation(graphql_document)

    @property
    @deprecated("Use 'pre_execution_errors' instead")
    def errors(self) -> list[GraphQLError] | None:
        """Deprecated: Use pre_execution_errors instead."""
        return self.pre_execution_errors


@dataclasses.dataclass
class ExecutionResult:
    data: dict[str, Any] | None
    errors: list[GraphQLError] | None
    extensions: dict[str, Any] | None = None


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
