import dataclasses
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, cast

from typing_extensions import Literal

from graphql import (
    ASTValidationRule,
    ExecutionResult as GraphQLExecutionResult,
    specified_rules,
)
from graphql.error.graphql_error import GraphQLError
from graphql.language import DocumentNode, OperationDefinitionNode


if TYPE_CHECKING:
    from strawberry.schema import Schema


graphql_operation_types = Literal["QUERY", "MUTATION"]


@dataclasses.dataclass
class ExecutionContext:
    query: str
    schema: "Schema"
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    root_value: Optional[Any] = None
    validation_rules: Tuple[Type[ASTValidationRule], ...] = dataclasses.field(
        default_factory=lambda: tuple(specified_rules)
    )

    # The operation name that is provided by the request
    _provided_operation_name: Optional[str] = None

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: Optional[DocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None

    @property
    def operation_name(self) -> Optional[str]:
        if self._provided_operation_name:
            return self._provided_operation_name

        definition = self._get_first_operation()
        if not definition:
            raise RuntimeError("Can't get GraphQL operation")

        if not definition.name:
            return None

        return definition.name.value

    @property
    def operation_type(self) -> graphql_operation_types:
        definition: Optional[OperationDefinitionNode] = None

        graphql_document = self.graphql_document
        if not graphql_document:
            raise RuntimeError("No GraphQL document available")

        # If no operation_name has been specified then use the first
        # OperationDefinitionNode
        if not self._provided_operation_name:
            definition = self._get_first_operation()
        else:
            for d in graphql_document.definitions:
                d = cast(OperationDefinitionNode, d)
                if d.name and d.name.value == self._provided_operation_name:
                    definition = d
                    break

        if not definition:
            raise RuntimeError("Can't get GraphQL operation type")

        return cast(graphql_operation_types, definition.operation.name)

    def _get_first_operation(self) -> Optional[OperationDefinitionNode]:
        graphql_document = self.graphql_document
        if not graphql_document:
            raise RuntimeError("No GraphQL document available")

        definition = next(
            (
                node
                for node in graphql_document.definitions
                if isinstance(node, OperationDefinitionNode)
            ),
            None,
        )
        return definition


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None
