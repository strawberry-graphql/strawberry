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


GraphqlOperationTypes = Literal["QUERY", "MUTATION"]


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
    provided_operation_name: dataclasses.InitVar[Optional[str]] = None

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: Optional[DocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None

    def __post_init__(self, provided_operation_name):
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
    def operation_type(self) -> GraphqlOperationTypes:
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

        return cast(GraphqlOperationTypes, definition.operation.name)

    def _get_first_operation(self) -> Optional[OperationDefinitionNode]:
        graphql_document = self.graphql_document
        if not graphql_document:
            return None

        definition: Optional[OperationDefinitionNode] = None
        for d in graphql_document.definitions:
            if isinstance(d, OperationDefinitionNode):
                definition = d
                break

        return definition


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None
