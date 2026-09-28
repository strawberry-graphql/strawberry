from typing import Any, TypeAlias, Union

from graphql import (
    ExperimentalIncrementalExecutionResults as GraphQLIncrementalExecutionResults,
)
from graphql.execution import ExecutionResult as OriginalGraphQLExecutionResult
from graphql.execution import (
    Executor as GraphQLExecutionContext,
)
from graphql.execution import (
    InitialIncrementalExecutionResult,
    SubsequentIncrementalExecutionResult,
    execute,
    experimental_execute_incrementally,
    subscribe,
)

# graphql-core only delivers `@defer`/`@stream` results from `IncrementalExecutor`,
# which is also what its own `execute` uses by default.
from graphql.execution.incremental import (
    IncrementalExecutor as BaseGraphQLExecutionContext,
)
from graphql.type.directives import GraphQLDeferDirective, GraphQLStreamDirective

from strawberry.types import ExecutionResult

incremental_execution_directives = (
    GraphQLDeferDirective,
    GraphQLStreamDirective,
)

GraphQLExecutionResult: TypeAlias = (
    OriginalGraphQLExecutionResult | InitialIncrementalExecutionResult
)

# The individual frames produced when an incremental delivery container
# (`@defer`/`@stream`) is expanded into a flat stream of results.
GraphQLIncrementalResult: TypeAlias = (
    InitialIncrementalExecutionResult | SubsequentIncrementalExecutionResult
)


def execution_context_class_kwargs(
    execution_context_class: type[GraphQLExecutionContext] | None,
) -> dict[str, Any]:
    if execution_context_class is None:
        return {}

    return {"executor_class": execution_context_class}


# TODO: give this a better name, maybe also a better place
ResultType = Union[  # noqa: UP007
    OriginalGraphQLExecutionResult,
    InitialIncrementalExecutionResult,
    GraphQLIncrementalExecutionResults,
    ExecutionResult,
]

__all__ = [
    "BaseGraphQLExecutionContext",
    "GraphQLExecutionContext",
    "GraphQLExecutionResult",
    "GraphQLIncrementalExecutionResults",
    "GraphQLIncrementalResult",
    "InitialIncrementalExecutionResult",
    "ResultType",
    "SubsequentIncrementalExecutionResult",
    "execute",
    "execution_context_class_kwargs",
    "experimental_execute_incrementally",
    "incremental_execution_directives",
    "subscribe",
]
