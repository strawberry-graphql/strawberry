from __future__ import annotations

import warnings
from asyncio import ensure_future
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Iterable
from functools import cached_property, lru_cache
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NamedTuple,
    Optional,
    Union,
    cast,
)

from graphql import ExecutionContext as GraphQLExecutionContext
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import (
    ExecutionResult as OriginalExecutionResult,
)
from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    GraphQLBoolean,
    GraphQLError,
    GraphQLField,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLSchema,
    OperationDefinitionNode,
    get_introspection_query,
    parse,
    validate_schema,
)
from graphql.execution import execute, subscribe
from graphql.execution.middleware import MiddlewareManager
from graphql.type.directives import specified_directives
from graphql.validation import validate

from strawberry import relay
from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import MissingQueryError
from strawberry.extensions import SchemaExtension
from strawberry.extensions.directives import (
    DirectivesExtension,
    DirectivesExtensionSync,
)
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.printer import print_schema
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema.validation_rules.one_of import OneOfInputValidationRule
from strawberry.types.base import (
    StrawberryObjectDefinition,
    WithStrawberryObjectDefinition,
    has_object_definition,
)
from strawberry.types.execution import (
    ExecutionContext,
    ExecutionResult,
    PreExecutionError,
)
from strawberry.types.graphql import OperationType
from strawberry.utils import IS_GQL_32, IS_GQL_33
from strawberry.utils.aio import aclosing
from strawberry.utils.await_maybe import await_maybe

from . import compat
from .base import BaseSchema
from .config import StrawberryConfig
from .exceptions import CannotGetOperationTypeError, InvalidOperationTypeError

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing_extensions import TypeAlias

    from graphql.execution.collect_fields import FieldGroup  # type: ignore
    from graphql.language import DocumentNode
    from graphql.pyutils import Path
    from graphql.type import GraphQLResolveInfo
    from graphql.validation import ASTValidationRule

    from strawberry.directive import StrawberryDirective
    from strawberry.types.base import StrawberryType
    from strawberry.types.enum import EnumDefinition
    from strawberry.types.field import StrawberryField
    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper
    from strawberry.types.union import StrawberryUnion

SubscriptionResult: TypeAlias = AsyncGenerator[
    Union[PreExecutionError, ExecutionResult], None
]

OriginSubscriptionResult = Union[
    OriginalExecutionResult,
    AsyncIterator[OriginalExecutionResult],
]

DEFAULT_ALLOWED_OPERATION_TYPES = {
    OperationType.QUERY,
    OperationType.MUTATION,
    OperationType.SUBSCRIPTION,
}
ProcessErrors: TypeAlias = (
    "Callable[[list[GraphQLError], Optional[ExecutionContext]], None]"
)


# TODO: merge with below
def validate_document(
    schema: GraphQLSchema,
    document: DocumentNode,
    validation_rules: tuple[type[ASTValidationRule], ...],
) -> list[GraphQLError]:
    validation_rules = (
        *validation_rules,
        OneOfInputValidationRule,
    )
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


def _coerce_error(error: Union[GraphQLError, Exception]) -> GraphQLError:
    if isinstance(error, GraphQLError):
        return error
    return GraphQLError(str(error), original_error=error)


class _OperationContextAwareGraphQLResolveInfo(NamedTuple):  # pyright: ignore
    field_name: str
    field_nodes: list[FieldNode]
    return_type: GraphQLOutputType
    parent_type: GraphQLObjectType
    path: Path
    schema: GraphQLSchema
    fragments: dict[str, FragmentDefinitionNode]
    root_value: Any
    operation: OperationDefinitionNode
    variable_values: dict[str, Any]
    context: Any
    is_awaitable: Callable[[Any], bool]
    operation_extensions: dict[str, Any]


class StrawberryGraphQLCoreExecutionContext(GraphQLExecutionContext):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        operation_extensions = kwargs.pop("operation_extensions", None)

        super().__init__(*args, **kwargs)

        self.operation_extensions = operation_extensions

    def build_resolve_info(
        self,
        field_def: GraphQLField,
        field_group: FieldGroup,
        parent_type: GraphQLObjectType,
        path: Path,
    ) -> GraphQLResolveInfo:
        if IS_GQL_33:
            return _OperationContextAwareGraphQLResolveInfo(  # type: ignore
                field_group.fields[0].node.name.value,
                field_group.to_nodes(),
                field_def.type,
                parent_type,
                path,
                self.schema,
                self.fragments,
                self.root_value,
                self.operation,
                self.variable_values,
                self.context_value,
                self.is_awaitable,
                self.operation_extensions,
            )

        return super().build_resolve_info(
            field_def,
            field_group,
            parent_type,
            path,
        )


class Schema(BaseSchema):
    def __init__(
        self,
        # TODO: can we make sure we only allow to pass
        # something that has been decorated?
        query: type,
        mutation: Optional[type] = None,
        subscription: Optional[type] = None,
        directives: Iterable[StrawberryDirective] = (),
        types: Iterable[Union[type, StrawberryType]] = (),
        extensions: Iterable[Union[type[SchemaExtension], SchemaExtension]] = (),
        execution_context_class: Optional[type[GraphQLExecutionContext]] = None,
        config: Optional[StrawberryConfig] = None,
        scalar_overrides: Optional[
            Mapping[object, Union[type, ScalarWrapper, ScalarDefinition]],
        ] = None,
        schema_directives: Iterable[object] = (),
    ) -> None:
        """Default Schema to be used in a Strawberry application.

        A GraphQL Schema class used to define the structure and configuration
        of GraphQL queries, mutations, and subscriptions.

        This class allows the creation of a GraphQL schema by specifying the types
        for queries, mutations, and subscriptions, along with various configuration
        options such as directives, extensions, and scalar overrides.

        Args:
            query: The entry point for queries.
            mutation: The entry point for mutations.
            subscription: The entry point for subscriptions.
            directives: A list of operation directives that clients can use.
                The bult-in `@include` and `@skip` are included by default.
            types: A list of additional types that will be included in the schema.
            extensions: A list of Strawberry extensions.
            execution_context_class: The execution context class.
            config: The configuration for the schema.
            scalar_overrides: A dictionary of overrides for scalars.
            schema_directives: A list of schema directives for the schema.

        Example:
        ```python
        import strawberry


        @strawberry.type
        class Query:
            name: str = "Patrick"


        schema = strawberry.Schema(query=Query)
        ```
        """
        self.query = query
        self.mutation = mutation
        self.subscription = subscription

        self.extensions = extensions
        self._cached_middleware_manager: MiddlewareManager | None = None
        self.execution_context_class = (
            execution_context_class or StrawberryGraphQLCoreExecutionContext
        )
        self.config = config or StrawberryConfig()

        self.schema_converter = GraphQLCoreConverter(
            self.config,
            scalar_overrides=scalar_overrides or {},  # type: ignore
            get_fields=self.get_fields,
        )

        self.directives = directives
        self.schema_directives = list(schema_directives)

        query_type = self.schema_converter.from_object(
            cast(
                "type[WithStrawberryObjectDefinition]", query
            ).__strawberry_definition__
        )
        mutation_type = (
            self.schema_converter.from_object(
                cast(
                    "type[WithStrawberryObjectDefinition]", mutation
                ).__strawberry_definition__
            )
            if mutation
            else None
        )
        subscription_type = (
            self.schema_converter.from_object(
                cast(
                    "type[WithStrawberryObjectDefinition]", subscription
                ).__strawberry_definition__
            )
            if subscription
            else None
        )

        graphql_directives = [
            self.schema_converter.from_directive(directive) for directive in directives
        ]

        graphql_types = []
        for type_ in types:
            if compat.is_schema_directive(type_):
                graphql_directives.append(
                    self.schema_converter.from_schema_directive(type_)
                )
            else:
                if (
                    has_object_definition(type_)
                    and type_.__strawberry_definition__.is_graphql_generic
                ):
                    type_ = StrawberryAnnotation(type_).resolve()  # noqa: PLW2901
                graphql_type = self.schema_converter.from_maybe_optional(type_)
                if isinstance(graphql_type, GraphQLNonNull):
                    graphql_type = graphql_type.of_type
                if not isinstance(graphql_type, GraphQLNamedType):
                    raise TypeError(f"{graphql_type} is not a named GraphQL Type")
                graphql_types.append(graphql_type)

        try:
            self._schema = GraphQLSchema(
                query=query_type,
                mutation=mutation_type,
                subscription=subscription_type if subscription else None,
                directives=specified_directives + tuple(graphql_directives),
                types=graphql_types,
                extensions={
                    GraphQLCoreConverter.DEFINITION_BACKREF: self,
                },
            )

        except TypeError as error:
            # GraphQL core throws a TypeError if there's any exception raised
            # during the schema creation, so we check if the cause was a
            # StrawberryError and raise it instead if that's the case.

            from strawberry.exceptions import StrawberryException

            if isinstance(error.__cause__, StrawberryException):
                raise error.__cause__ from None

            raise

        # attach our schema to the GraphQL schema instance
        self._schema._strawberry_schema = self  # type: ignore

        self._warn_for_federation_directives()
        self._resolve_node_ids()
        self._extend_introspection()

        # Validate schema early because we want developers to know about
        # possible issues as soon as possible
        errors = validate_schema(self._schema)
        if errors:
            formatted_errors = "\n\n".join(f"❌ {error.message}" for error in errors)
            raise ValueError(f"Invalid Schema. Errors:\n\n{formatted_errors}")

    def get_extensions(self, sync: bool = False) -> list[SchemaExtension]:
        extensions: list[type[SchemaExtension] | SchemaExtension] = []
        extensions.extend(self.extensions)
        if self.directives:
            extensions.extend(
                [DirectivesExtensionSync if sync else DirectivesExtension]
            )
        return [
            ext if isinstance(ext, SchemaExtension) else ext(execution_context=None)
            for ext in extensions
        ]

    @cached_property
    def _sync_extensions(self) -> list[SchemaExtension]:
        return self.get_extensions(sync=True)

    @cached_property
    def _async_extensions(self) -> list[SchemaExtension]:
        return self.get_extensions(sync=False)

    def create_extensions_runner(
        self, execution_context: ExecutionContext, extensions: list[SchemaExtension]
    ) -> SchemaExtensionsRunner:
        return SchemaExtensionsRunner(
            execution_context=execution_context,
            extensions=extensions,
        )

    def _get_custom_context_kwargs(
        self, operation_extensions: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        if not IS_GQL_33:
            return {}

        return {"operation_extensions": operation_extensions}

    def _get_middleware_manager(
        self, extensions: list[SchemaExtension]
    ) -> MiddlewareManager:
        # create a middleware manager with all the extensions that implement resolve
        if not self._cached_middleware_manager:
            self._cached_middleware_manager = MiddlewareManager(
                *(ext for ext in extensions if ext._implements_resolve())
            )
        return self._cached_middleware_manager

    def _create_execution_context(
        self,
        query: Optional[str],
        allowed_operation_types: Iterable[OperationType],
        variable_values: Optional[dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        operation_extensions: Optional[dict[str, Any]] = None,
    ) -> ExecutionContext:
        return ExecutionContext(
            query=query,
            schema=self,
            allowed_operations=allowed_operation_types,
            context=context_value,
            root_value=root_value,
            variables=variable_values,
            provided_operation_name=operation_name,
            operation_extensions=operation_extensions,
        )

    @lru_cache
    def get_type_by_name(
        self, name: str
    ) -> Optional[
        Union[
            StrawberryObjectDefinition,
            ScalarDefinition,
            EnumDefinition,
            StrawberryUnion,
        ]
    ]:
        # TODO: respect auto_camel_case
        if name in self.schema_converter.type_map:
            return self.schema_converter.type_map[name].definition

        return None

    def get_field_for_type(
        self, field_name: str, type_name: str
    ) -> Optional[StrawberryField]:
        type_ = self.get_type_by_name(type_name)

        if not type_:
            return None  # pragma: no cover

        assert isinstance(type_, StrawberryObjectDefinition)

        return next(
            (
                field
                for field in type_.fields
                if self.config.name_converter.get_graphql_name(field) == field_name
            ),
            None,
        )

    @lru_cache
    def get_directive_by_name(self, graphql_name: str) -> Optional[StrawberryDirective]:
        return next(
            (
                directive
                for directive in self.directives
                if self.config.name_converter.from_directive(directive) == graphql_name
            ),
            None,
        )

    def get_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> list[StrawberryField]:
        return type_definition.fields

    async def _parse_and_validate_async(
        self, context: ExecutionContext, extensions_runner: SchemaExtensionsRunner
    ) -> Optional[PreExecutionError]:
        if not context.query:
            raise MissingQueryError

        async with extensions_runner.parsing():
            try:
                if not context.graphql_document:
                    context.graphql_document = parse(context.query)

            except GraphQLError as error:
                context.errors = [error]
                return PreExecutionError(data=None, errors=[error])

            except Exception as error:  # noqa: BLE001
                error = GraphQLError(str(error), original_error=error)
                context.errors = [error]
                return PreExecutionError(data=None, errors=[error])

        try:
            operation_type = context.operation_type
        except RuntimeError as error:
            raise CannotGetOperationTypeError(context.operation_name) from error

        if operation_type not in context.allowed_operations:
            raise InvalidOperationTypeError(operation_type)

        async with extensions_runner.validation():
            _run_validation(context)
            if context.errors:
                return PreExecutionError(
                    data=None,
                    errors=context.errors,
                )

        return None

    async def _handle_execution_result(
        self,
        context: ExecutionContext,
        result: Union[GraphQLExecutionResult, ExecutionResult],
        extensions_runner: SchemaExtensionsRunner,
        *,
        # TODO: can we remove this somehow, see comment in execute
        skip_process_errors: bool = False,
    ) -> ExecutionResult:
        # Set errors on the context so that it's easier
        # to access in extensions
        if result.errors:
            context.errors = result.errors
            if not skip_process_errors:
                self._process_errors(result.errors, context)
        if isinstance(result, GraphQLExecutionResult):
            result = ExecutionResult(data=result.data, errors=result.errors)
        result.extensions = await extensions_runner.get_extensions_results(context)
        context.result = result  # type: ignore  # mypy failed to deduce correct type.
        return result

    async def execute(
        self,
        query: Optional[str],
        variable_values: Optional[dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
        operation_extensions: Optional[dict[str, Any]] = None,
    ) -> ExecutionResult:
        if allowed_operation_types is None:
            allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES

        execution_context = self._create_execution_context(
            query=query,
            allowed_operation_types=allowed_operation_types,
            variable_values=variable_values,
            context_value=context_value,
            root_value=root_value,
            operation_name=operation_name,
            operation_extensions=operation_extensions,
        )
        extensions = self.get_extensions()
        # TODO (#3571): remove this when we implement execution context as parameter.
        for extension in extensions:
            extension.execution_context = execution_context

        extensions_runner = self.create_extensions_runner(execution_context, extensions)
        middleware_manager = self._get_middleware_manager(extensions)

        custom_context_kwargs = self._get_custom_context_kwargs(operation_extensions)

        try:
            async with extensions_runner.operation():
                # Note: In graphql-core the schema would be validated here but in
                # Strawberry we are validating it at initialisation time instead

                if errors := await self._parse_and_validate_async(
                    execution_context, extensions_runner
                ):
                    return await self._handle_execution_result(
                        execution_context,
                        errors,
                        extensions_runner,
                    )

                assert execution_context.graphql_document
                async with extensions_runner.executing():
                    if not execution_context.result:
                        result = await await_maybe(
                            execute(
                                self._schema,
                                execution_context.graphql_document,
                                root_value=execution_context.root_value,
                                middleware=middleware_manager,
                                variable_values=execution_context.variables,
                                operation_name=execution_context.operation_name,
                                context_value=execution_context.context,
                                execution_context_class=self.execution_context_class,
                                **custom_context_kwargs,
                            )
                        )
                        execution_context.result = result
                    else:
                        result = execution_context.result
                    # Also set errors on the execution_context so that it's easier
                    # to access in extensions
                    if result.errors:
                        execution_context.errors = result.errors

                        # Run the `Schema.process_errors` function here before
                        # extensions have a chance to modify them (see the MaskErrors
                        # extension). That way we can log the original errors but
                        # only return a sanitised version to the client.
                        self._process_errors(result.errors, execution_context)

        except (
            MissingQueryError,
            CannotGetOperationTypeError,
            InvalidOperationTypeError,
        ):
            raise
        except Exception as exc:  # noqa: BLE001
            return await self._handle_execution_result(
                execution_context,
                PreExecutionError(data=None, errors=[_coerce_error(exc)]),
                extensions_runner,
            )
        # return results after all the operation completed.
        return await self._handle_execution_result(
            execution_context, result, extensions_runner, skip_process_errors=True
        )

    def execute_sync(
        self,
        query: Optional[str],
        variable_values: Optional[dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
        operation_extensions: Optional[dict[str, Any]] = None,
    ) -> ExecutionResult:
        if allowed_operation_types is None:
            allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES

        execution_context = self._create_execution_context(
            query=query,
            allowed_operation_types=allowed_operation_types,
            variable_values=variable_values,
            context_value=context_value,
            root_value=root_value,
            operation_name=operation_name,
            operation_extensions=operation_extensions,
        )
        extensions = self._sync_extensions
        # TODO (#3571): remove this when we implement execution context as parameter.
        for extension in extensions:
            extension.execution_context = execution_context

        extensions_runner = self.create_extensions_runner(execution_context, extensions)
        middleware_manager = self._get_middleware_manager(extensions)

        custom_context_kwargs = self._get_custom_context_kwargs(operation_extensions)

        try:
            with extensions_runner.operation():
                # Note: In graphql-core the schema would be validated here but in
                # Strawberry we are validating it at initialisation time instead
                if not execution_context.query:
                    raise MissingQueryError  # noqa: TRY301

                with extensions_runner.parsing():
                    try:
                        if not execution_context.graphql_document:
                            execution_context.graphql_document = parse(
                                execution_context.query,
                                **execution_context.parse_options,
                            )

                    except GraphQLError as error:
                        execution_context.errors = [error]
                        self._process_errors([error], execution_context)
                        return ExecutionResult(
                            data=None,
                            errors=[error],
                            extensions=extensions_runner.get_extensions_results_sync(),
                        )

                try:
                    operation_type = execution_context.operation_type
                except RuntimeError as error:
                    raise CannotGetOperationTypeError(
                        execution_context.operation_name
                    ) from error

                if operation_type not in execution_context.allowed_operations:
                    raise InvalidOperationTypeError(operation_type)  # noqa: TRY301

                with extensions_runner.validation():
                    _run_validation(execution_context)
                    if execution_context.errors:
                        self._process_errors(
                            execution_context.errors, execution_context
                        )
                        return ExecutionResult(
                            data=None,
                            errors=execution_context.errors,
                            extensions=extensions_runner.get_extensions_results_sync(),
                        )

                with extensions_runner.executing():
                    if not execution_context.result:
                        result = execute(
                            self._schema,
                            execution_context.graphql_document,
                            root_value=execution_context.root_value,
                            middleware=middleware_manager,
                            variable_values=execution_context.variables,
                            operation_name=execution_context.operation_name,
                            context_value=execution_context.context,
                            execution_context_class=self.execution_context_class,
                            **custom_context_kwargs,
                        )

                        if isawaitable(result):
                            result = cast("Awaitable[GraphQLExecutionResult]", result)  # type: ignore[redundant-cast]
                            ensure_future(result).cancel()
                            raise RuntimeError(  # noqa: TRY301
                                "GraphQL execution failed to complete synchronously."
                            )

                        result = cast("GraphQLExecutionResult", result)  # type: ignore[redundant-cast]
                        execution_context.result = result
                        # Also set errors on the context so that it's easier
                        # to access in extensions
                        if result.errors:
                            execution_context.errors = result.errors

                            # Run the `Schema.process_errors` function here before
                            # extensions have a chance to modify them (see the MaskErrors
                            # extension). That way we can log the original errors but
                            # only return a sanitised version to the client.
                            self._process_errors(result.errors, execution_context)
        except (
            MissingQueryError,
            CannotGetOperationTypeError,
            InvalidOperationTypeError,
        ):
            raise
        except Exception as exc:  # noqa: BLE001
            errors = [_coerce_error(exc)]
            execution_context.errors = errors
            self._process_errors(errors, execution_context)
            return ExecutionResult(
                data=None,
                errors=errors,
                extensions=extensions_runner.get_extensions_results_sync(),
            )
        return ExecutionResult(
            data=execution_context.result.data,
            errors=execution_context.result.errors,
            extensions=extensions_runner.get_extensions_results_sync(),
        )

    async def _subscribe(
        self,
        execution_context: ExecutionContext,
        extensions_runner: SchemaExtensionsRunner,
        middleware_manager: MiddlewareManager,
        execution_context_class: type[GraphQLExecutionContext] | None = None,
        operation_extensions: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[ExecutionResult, None]:
        async with extensions_runner.operation():
            if initial_error := await self._parse_and_validate_async(
                context=execution_context,
                extensions_runner=extensions_runner,
            ):
                initial_error.extensions = (
                    await extensions_runner.get_extensions_results(execution_context)
                )
                yield await self._handle_execution_result(
                    execution_context, initial_error, extensions_runner
                )
            try:
                async with extensions_runner.executing():
                    assert execution_context.graphql_document is not None
                    gql_33_kwargs = {
                        "middleware": middleware_manager,
                        "execution_context_class": execution_context_class,
                        "operation_extensions": operation_extensions,
                    }
                    try:
                        # Might not be awaitable for pre-execution errors.
                        aiter_or_result: OriginSubscriptionResult = await await_maybe(
                            subscribe(
                                self._schema,
                                execution_context.graphql_document,
                                root_value=execution_context.root_value,
                                variable_values=execution_context.variables,
                                operation_name=execution_context.operation_name,
                                context_value=execution_context.context,
                                **{} if IS_GQL_32 else gql_33_kwargs,  # type: ignore[arg-type]
                            )
                        )
                    # graphql-core 3.2 doesn't handle some of the pre-execution errors.
                    # see `test_subscription_immediate_error`
                    except Exception as exc:  # noqa: BLE001
                        aiter_or_result = OriginalExecutionResult(
                            data=None, errors=[_coerce_error(exc)]
                        )

                # Handle pre-execution errors.
                if isinstance(aiter_or_result, OriginalExecutionResult):
                    yield await self._handle_execution_result(
                        execution_context,
                        PreExecutionError(data=None, errors=aiter_or_result.errors),
                        extensions_runner,
                    )
                else:
                    try:
                        async with aclosing(aiter_or_result):
                            async for result in aiter_or_result:
                                yield await self._handle_execution_result(
                                    execution_context,
                                    result,
                                    extensions_runner,
                                )
                    # graphql-core doesn't handle exceptions raised while executing.
                    except Exception as exc:  # noqa: BLE001
                        yield await self._handle_execution_result(
                            execution_context,
                            OriginalExecutionResult(
                                data=None, errors=[_coerce_error(exc)]
                            ),
                            extensions_runner,
                        )
            # catch exceptions raised in `on_execute` hook.
            except Exception as exc:  # noqa: BLE001
                origin_result = OriginalExecutionResult(
                    data=None, errors=[_coerce_error(exc)]
                )
                yield await self._handle_execution_result(
                    execution_context,
                    origin_result,
                    extensions_runner,
                )

    async def subscribe(
        self,
        query: Optional[str],
        variable_values: Optional[dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        operation_extensions: Optional[dict[str, Any]] = None,
    ) -> SubscriptionResult:
        execution_context = self._create_execution_context(
            query=query,
            allowed_operation_types=(OperationType.SUBSCRIPTION,),
            variable_values=variable_values,
            context_value=context_value,
            root_value=root_value,
            operation_name=operation_name,
        )
        extensions = self._async_extensions
        # TODO (#3571): remove this when we implement execution context as parameter.
        for extension in extensions:
            extension.execution_context = execution_context

        return self._subscribe(
            execution_context,
            extensions_runner=self.create_extensions_runner(
                execution_context, extensions
            ),
            middleware_manager=self._get_middleware_manager(extensions),
            execution_context_class=self.execution_context_class,
            operation_extensions=operation_extensions,
        )

    def _resolve_node_ids(self) -> None:
        for concrete_type in self.schema_converter.type_map.values():
            type_def = concrete_type.definition

            # This can be a TypeDefinition, EnumDefinition, ScalarDefinition
            # or UnionDefinition
            if not isinstance(type_def, StrawberryObjectDefinition):
                continue

            # Do not validate id_attr for interfaces. relay.Node itself and
            # any other interfdace that implements it are not required to
            # provide a NodeID annotation, only the concrete type implementing
            # them needs to do that.
            if type_def.is_interface:
                continue

            # Call resolve_id_attr in here to make sure we raise provide
            # early feedback for missing NodeID annotations
            origin = type_def.origin
            if issubclass(origin, relay.Node):
                has_custom_resolve_id = False
                for base in origin.__mro__:
                    if base is relay.Node:
                        break
                    if "resolve_id" in base.__dict__:
                        has_custom_resolve_id = True
                        break

                if not has_custom_resolve_id:
                    origin.resolve_id_attr()

    def _warn_for_federation_directives(self) -> None:
        """Raises a warning if the schema has any federation directives."""
        from strawberry.federation.schema_directives import FederationDirective

        all_types = self.schema_converter.type_map.values()
        all_type_defs = (type_.definition for type_ in all_types)

        all_directives = (
            directive
            for type_def in all_type_defs
            for directive in (type_def.directives or [])
        )

        if any(
            isinstance(directive, FederationDirective) for directive in all_directives
        ):
            warnings.warn(
                "Federation directive found in schema. "
                "Use `strawberry.federation.Schema` instead of `strawberry.Schema`.",
                UserWarning,
                stacklevel=3,
            )

    def _extend_introspection(self) -> None:
        def _resolve_is_one_of(obj: Any, info: Any) -> bool:
            if "strawberry-definition" not in obj.extensions:
                return False

            return obj.extensions["strawberry-definition"].is_one_of

        instrospection_type = self._schema.type_map["__Type"]
        instrospection_type.fields["isOneOf"] = GraphQLField(GraphQLBoolean)  # type: ignore[attr-defined]
        instrospection_type.fields["isOneOf"].resolve = _resolve_is_one_of  # type: ignore[attr-defined]

    def as_str(self) -> str:
        return print_schema(self)

    __str__ = as_str

    def introspect(self) -> dict[str, Any]:
        """Return the introspection query result for the current schema.

        Raises:
            ValueError: If the introspection query fails due to an invalid schema
        """
        introspection = self.execute_sync(get_introspection_query())
        if introspection.errors or not introspection.data:
            raise ValueError(f"Invalid Schema. Errors {introspection.errors!r}")

        return introspection.data


__all__ = ["Schema"]
