from typing import Union

from graphql.execution import ExecutionContext as GraphQLExecutionContext
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from graphql.execution import execute, subscribe

from strawberry.types import ExecutionResult

try:
    from graphql import (
        ExperimentalIncrementalExecutionResults as GraphQLIncrementalExecutionResults,
    )
    from graphql.execution import experimental_execute_incrementally
    from graphql.type.directives import (
        GraphQLDeferDirective,
        GraphQLStreamDirective,
    )

    incremental_execution_directives = (
        GraphQLDeferDirective,
        GraphQLStreamDirective,
    )

except ImportError:
    GraphQLIncrementalExecutionResults = type(None)

    incremental_execution_directives = []
    experimental_execute_incrementally = None


# TODO: give this a better name, maybe also a better place
ResultType = Union[
    GraphQLExecutionResult,
    GraphQLIncrementalExecutionResults,
    ExecutionResult,
]

__all__ = [
    "GraphQLExecutionContext",
    "GraphQLIncrementalExecutionResults",
    "ResultType",
    "execute",
    "experimental_execute_incrementally",
    "incremental_execution_directives",
    "subscribe",
]
