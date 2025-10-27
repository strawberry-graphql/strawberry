from typing import TypeAlias, Union

from graphql.execution import ExecutionContext as GraphQLExecutionContext
from graphql.execution import ExecutionResult as OriginalGraphQLExecutionResult
from graphql.execution import execute, subscribe

from strawberry.types import ExecutionResult

try:
    from graphql import (  # type: ignore[attr-defined]
        ExperimentalIncrementalExecutionResults as GraphQLIncrementalExecutionResults,
    )
    from graphql.execution import (  # type: ignore[attr-defined]
        InitialIncrementalExecutionResult,
        experimental_execute_incrementally,
    )
    from graphql.type.directives import (  # type: ignore[attr-defined]
        GraphQLDeferDirective,
        GraphQLStreamDirective,
    )

    incremental_execution_directives = (
        GraphQLDeferDirective,
        GraphQLStreamDirective,
    )

    GraphQLExecutionResult: TypeAlias = (
        OriginalGraphQLExecutionResult | InitialIncrementalExecutionResult
    )

except ImportError:
    GraphQLIncrementalExecutionResults = type(None)
    GraphQLExecutionResult = OriginalGraphQLExecutionResult  # type: ignore

    incremental_execution_directives = ()  # type: ignore
    experimental_execute_incrementally = None


# TODO: give this a better name, maybe also a better place
ResultType = Union[  # noqa: UP007
    OriginalGraphQLExecutionResult,
    GraphQLIncrementalExecutionResults,
    ExecutionResult,
]

__all__ = [
    "GraphQLExecutionContext",
    "GraphQLExecutionResult",
    "GraphQLIncrementalExecutionResults",
    "ResultType",
    "execute",
    "experimental_execute_incrementally",
    "incremental_execution_directives",
    "subscribe",
]
