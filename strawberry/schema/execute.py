from asyncio import ensure_future
from inspect import isawaitable
from typing import (
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from graphql import ExecutionContext as GraphQLExecutionContext
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError, GraphQLSchema, parse
from graphql import execute as original_execute
from graphql.language import DocumentNode
from graphql.validation import ASTValidationRule, validate

from strawberry.extensions import Extension
from strawberry.extensions.runner import ExtensionsRunner
from strawberry.types import ExecutionContext, ExecutionResult
from strawberry.types.graphql import OperationType

from .exceptions import InvalidOperationTypeError


def parse_document(query: str) -> DocumentNode:
    return parse(query)


def validate_document(
    schema: GraphQLSchema,
    document: DocumentNode,
    validation_rules: Tuple[Type[ASTValidationRule], ...],
) -> List[GraphQLError]:
    return validate(
        schema,
        document,
        validation_rules,
    )


def _run_validation(execution_context: ExecutionContext) -> None:
    # Check if there are any validation rules or if validation has
    # already been run by an extension
    if len(execution_context.validation_rules) > 0 and execution_context.errors is None:
        assert execution_context.graphql_document
        execution_context.errors = validate_document(
            execution_context.schema._schema,
            execution_context.graphql_document,
            execution_context.validation_rules,
        )


def execute_sync(
    schema: GraphQLSchema,
    query: str,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[Union[Type[Extension], Extension]],
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
) -> ExecutionResult:
    extensions_runner = ExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        with extensions_runner.parsing():
            try:
                if not execution_context.graphql_document:
                    execution_context.graphql_document = parse_document(query)

            except GraphQLError as error:
                execution_context.errors = [error]
                process_errors([error], execution_context)
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

            except Exception as error:  # pragma: no cover
                error = GraphQLError(str(error), original_error=error)

                execution_context.errors = [error]
                process_errors([error], execution_context)

                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

        if execution_context.operation_type not in allowed_operation_types:
            raise InvalidOperationTypeError(execution_context.operation_type)

        with extensions_runner.validation():
            _run_validation(execution_context)
            if execution_context.errors:
                process_errors(execution_context.errors, execution_context)
                return ExecutionResult(data=None, errors=execution_context.errors)

        with extensions_runner.executing():
            if not execution_context.result:
                result = original_execute(
                    schema,
                    execution_context.graphql_document,
                    root_value=execution_context.root_value,
                    middleware=extensions_runner.as_middleware_manager(),
                    variable_values=execution_context.variables,
                    operation_name=execution_context.operation_name,
                    context_value=execution_context.context,
                    execution_context_class=execution_context_class,
                )

                if isawaitable(result):
                    result = cast(Awaitable[GraphQLExecutionResult], result)
                    ensure_future(result).cancel()
                    raise RuntimeError(
                        "GraphQL execution failed to complete synchronously."
                    )

                result = cast(GraphQLExecutionResult, result)
                execution_context.result = result
                # Also set errors on the execution_context so that it's easier
                # to access in extensions
                if result.errors:
                    execution_context.errors = result.errors

                    # Run the `Schema.process_errors` function here before
                    # extensions have a chance to modify them (see the MaskErrors
                    # extension). That way we can log the original errors but
                    # only return a sanitised version to the client.
                    process_errors(result.errors, execution_context)

    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=extensions_runner.get_extensions_results_sync(),
    )


class AsyncExecutionBase:
    def __init__(
        self,
        schema: GraphQLSchema,
        allowed_operation_types: Iterable[OperationType],
        extensions: Sequence[Union[Type[Extension], Extension]],
        execution_context: ExecutionContext,
        process_errors: Callable[
            [List[GraphQLError], Optional[ExecutionContext]], None
        ],
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    ):
        self.schema = schema
        self.query = execution_context.query
        self.execution_context = execution_context
        self.extensions = extensions
        self.execution_context_class = execution_context_class
        self.process_errors = process_errors
        self.allowed_operation_types = allowed_operation_types
        self.extensions_runner = ExtensionsRunner(
            execution_context=self.execution_context,
            extensions=list(self.extensions),
        )

    async def _parse_and_validate_runner(self) -> Optional[ExecutionResult]:
        async with self.extensions_runner.parsing():
            try:
                if not self.execution_context.graphql_document:
                    self.execution_context.graphql_document = parse_document(self.query)

            except GraphQLError as error:
                self.execution_context.errors = [error]
                self.process_errors([error], self.execution_context)
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=await self.extensions_runner.get_extensions_results(),
                    validation_error=True,
                )

            except Exception as error:
                error = GraphQLError(str(error), original_error=error)

                self.execution_context.errors = [error]
                self.process_errors([error], self.execution_context)

                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=await self.extensions_runner.get_extensions_results(),
                    validation_error=True,
                )

        if self.execution_context.operation_type not in self.allowed_operation_types:
            raise InvalidOperationTypeError(self.execution_context.operation_type)

        async with self.extensions_runner.validation():
            _run_validation(self.execution_context)
            if self.execution_context.errors:
                self.process_errors(
                    self.execution_context.errors, self.execution_context
                )
                return ExecutionResult(
                    data=None,
                    errors=self.execution_context.errors,
                    validation_error=True,
                )

    def _handle_execution_result(
        self,
        result: GraphQLExecutionResult,
    ) -> ExecutionResult:
        context = self.execution_context
        context.result = result
        # Also set errors on the execution_context so that it's easier
        # to access in extensions
        if result.errors:
            context.errors = result.errors

            # Run the `Schema.process_errors` function here before
            # extensions have a chance to modify them (see the MaskErrors
            # extension). That way we can log the original errors but
            # only return a sanitised version to the client.
            self.process_errors(result.errors, context)

        return ExecutionResult(
            data=result.data,
            errors=result.errors,
        )


class AsyncExecution(AsyncExecutionBase):
    async def execute(self) -> ExecutionResult:
        async with self.extensions_runner.operation():
            # Note: In graphql-core the schema would be validated here but in
            # Strawberry we are validating it at initialisation time instead

            ret = await self._parse_and_validate_runner()
            assert self.execution_context.graphql_document
            # if there was no parsing error
            if not ret:
                ret = ExecutionResult()
                async with self.extensions_runner.executing():
                    if not self.execution_context.result:
                        result = original_execute(
                            self.schema,
                            self.execution_context.graphql_document,
                            root_value=self.execution_context.root_value,
                            middleware=self.extensions_runner.as_middleware_manager(),
                            variable_values=self.execution_context.variables,
                            operation_name=self.execution_context.operation_name,
                            context_value=self.execution_context.context,
                            execution_context_class=self.execution_context_class,
                        )

                        if isawaitable(result):
                            result = await cast(
                                Awaitable[GraphQLExecutionResult], result
                            )
                        result = cast(GraphQLExecutionResult, result)
                        ret = self._handle_execution_result(
                            result=result,
                        )
                    else:
                        ret.data = self.execution_context.result.data
        ret.extensions = await self.extensions_runner.get_extensions_results()
        return ret
