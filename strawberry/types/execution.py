import dataclasses
from typing import Any, Collection, Dict, List, Optional, Type, Union

from graphql import (
    ASTValidationRule,
    ExecutionResult as GraphQLExecutionResult,
    GraphQLSchema,
    specified_rules,
)
from graphql.error.graphql_error import GraphQLError
from graphql.language import DocumentNode
from graphql.pyutils import FrozenList


@dataclasses.dataclass
class ExecutionContext:
    query: str
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None
    root_value: Optional[Any] = None
    graphql_schema: Optional[GraphQLSchema] = None
    validation_rules: Union[
        Collection[Type[ASTValidationRule]], FrozenList[Type[ASTValidationRule]]
    ] = dataclasses.field(default_factory=lambda: specified_rules)

    # Values that get populated during the GraphQL execution so that they can be
    # accessed by extensions
    graphql_document: Optional[DocumentNode] = None
    errors: Optional[List[GraphQLError]] = None
    result: Optional[GraphQLExecutionResult] = None


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None
