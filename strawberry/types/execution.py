import dataclasses
from typing import Any, Dict, List, Optional

from graphql.error.graphql_error import GraphQLError


@dataclasses.dataclass
class ExecutionContext:
    query: str
    context: Any = None
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None


@dataclasses.dataclass
class ExecutionResult:
    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    extensions: Optional[Dict[str, Any]] = None
