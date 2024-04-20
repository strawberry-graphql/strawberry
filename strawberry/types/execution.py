from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
)
from typing_extensions import TypedDict

from graphql import specified_rules

from strawberry.utils.operation import get_first_operation, get_operation_type

if TYPE_CHECKING:
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
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    parse_options: ParseOptions = dataclasses.field(
        default_factory=lambda: ParseOptions()
    )
    root_value: Optional[Any] = None
    validation_rules: Tuple[Type[ASTValidationRule], ...] = dataclasses.field(
        default_factory=lambda: tuple(specified_rules)
    )

    # The operation name that is provided by the request
    provided_operation_name: dataclasses.InitVar[Optional[str]] = None

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: Optional[DocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None

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
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None


class ParseOptions(TypedDict):
    max_tokens: NotRequired[int]
