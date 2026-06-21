from typing import Any, TypeAlias, Union

try:
    from graphql.execution import ExecutionContext as GraphQLExecutionContext

    _execution_context_class_arg = "execution_context_class"
except ImportError:
    from graphql.execution import (  # type: ignore[attr-defined,no-redef]
        Executor as GraphQLExecutionContext,  # pyright: ignore[reportAttributeAccessIssue]
    )

    _execution_context_class_arg = "executor_class"

from graphql.execution import ExecutionResult as OriginalGraphQLExecutionResult
from graphql.execution import execute, subscribe

from strawberry.types import ExecutionResult

try:
    from graphql import (  # type: ignore[attr-defined]
        ExperimentalIncrementalExecutionResults as GraphQLIncrementalExecutionResults,  # pyright: ignore[reportAttributeAccessIssue]
    )
    from graphql.execution import (  # type: ignore[attr-defined]
        InitialIncrementalExecutionResult,  # pyright: ignore[reportAttributeAccessIssue]
        SubsequentIncrementalExecutionResult,  # pyright: ignore[reportAttributeAccessIssue]
        experimental_execute_incrementally,  # pyright: ignore[reportAttributeAccessIssue]
    )
    from graphql.type.directives import (  # type: ignore[attr-defined]
        GraphQLDeferDirective,  # pyright: ignore[reportAttributeAccessIssue]
        GraphQLStreamDirective,  # pyright: ignore[reportAttributeAccessIssue]
    )

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

except ImportError:

    class GraphQLIncrementalExecutionResults:  # type: ignore[no-redef]
        pass

    class InitialIncrementalExecutionResult:  # type: ignore[no-redef]
        pass

    class SubsequentIncrementalExecutionResult:  # type: ignore[no-redef]
        pass

    GraphQLExecutionResult = OriginalGraphQLExecutionResult  # type: ignore
    # Incremental delivery isn't available on graphql-core < 3.3, so no frame
    # type exists. Fall back to the (empty) container type so annotations remain
    # importable at runtime.
    GraphQLIncrementalResult = GraphQLIncrementalExecutionResults  # type: ignore

    incremental_execution_directives = ()  # type: ignore
    experimental_execute_incrementally = None


def execution_context_class_kwargs(
    execution_context_class: type[GraphQLExecutionContext] | None,
) -> dict[str, Any]:
    if execution_context_class is None:
        return {}

    return {_execution_context_class_arg: execution_context_class}


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
