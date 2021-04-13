import logging
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from graphql import (
    ExecutionContext as GraphQLExecutionContext,
    GraphQLSchema,
    get_introspection_query,
    parse,
    validate_schema,
)
from graphql.error import GraphQLError
from graphql.subscription import subscribe
from graphql.type.directives import specified_directives

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.extensions import Extension
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.types import ExecutionResult
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion

from ..middleware import DirectivesMiddleware, Middleware
from ..printer import print_schema
from .execute import execute, execute_sync


logger = logging.getLogger("strawberry.execution")


class Schema:
    def __init__(
        self,
        # TODO: can we make sure we only allow to pass something that has been decorated?
        query: Type,
        mutation: Optional[Type] = None,
        subscription: Optional[Type] = None,
        directives=(),
        types=(),
        extensions: Sequence[Type[Extension]] = (),
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    ):
        self.extensions = extensions
        self.execution_context_class = execution_context_class
        self.schema_converter = GraphQLCoreConverter()

        query_type = self.schema_converter.from_object_type(query)
        mutation_type = (
            self.schema_converter.from_object_type(mutation) if mutation else None
        )
        subscription_type = (
            self.schema_converter.from_object_type(subscription)
            if subscription
            else None
        )

        self.middleware: List[Middleware] = [DirectivesMiddleware(directives)]

        directives = [
            self.schema_converter.from_directive(directive.directive_definition)
            for directive in directives
        ]

        self._schema = GraphQLSchema(
            query=query_type,
            mutation=mutation_type,
            subscription=subscription_type if subscription else None,
            directives=specified_directives + directives,
            types=list(map(self.schema_converter.from_object_type, types)),
        )

        # Validate schema early because we want developers to know about
        # possible issues as soon as possible
        errors = validate_schema(self._schema)
        if errors:
            formatted_errors = "\n\n".join(f"❌ {error.message}" for error in errors)
            raise ValueError(f"Invalid Schema. Errors:\n\n{formatted_errors}")

        self.query = self.schema_converter.type_map[query_type.name]

    def get_type_by_name(
        self, name: str
    ) -> Optional[
        Union[TypeDefinition, ScalarDefinition, EnumDefinition, StrawberryUnion]
    ]:
        if name in self.schema_converter.type_map:
            return self.schema_converter.type_map[name].definition

        return None

    def process_errors(self, errors: List[GraphQLError]) -> None:
        for error in errors:
            actual_error = error.original_error or error
            logger.error(actual_error, exc_info=actual_error)

    async def execute(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        validate_queries: bool = True,
    ) -> ExecutionResult:
        result = await execute(
            self._schema,
            query,
            variable_values=variable_values,
            root_value=root_value,
            context_value=context_value,
            operation_name=operation_name,
            additional_middlewares=self.middleware,
            extensions=self.extensions,
            execution_context_class=self.execution_context_class,
            validate_queries=validate_queries,
        )

        if result.errors:
            self.process_errors(result.errors)

        return ExecutionResult(
            data=result.data,
            errors=result.errors,
            extensions=result.extensions,
        )

    def execute_sync(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        validate_queries: bool = True,
    ) -> ExecutionResult:
        result = execute_sync(
            self._schema,
            query,
            variable_values=variable_values,
            root_value=root_value,
            context_value=context_value,
            operation_name=operation_name,
            additional_middlewares=self.middleware,
            extensions=self.extensions,
            execution_context_class=self.execution_context_class,
            validate_queries=validate_queries,
        )

        if result.errors:
            self.process_errors(result.errors)

        return ExecutionResult(
            data=result.data,
            errors=result.errors,
            extensions=result.extensions,
        )

    async def subscribe(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ):
        return await subscribe(
            self._schema,
            parse(query),
            root_value=root_value,
            context_value=context_value,
            variable_values=variable_values,
            operation_name=operation_name,
        )

    def as_str(self) -> str:
        return print_schema(self)

    __str__ = as_str

    def introspect(self) -> Dict[str, Any]:
        """Return the introspection query result for the current schema

        Raises:
            ValueError: If the introspection query fails due to an invalid schema
        """
        introspection = self.execute_sync(get_introspection_query())
        if introspection.errors or not introspection.data:
            raise ValueError(f"Invalid Schema. Errors {introspection.errors!r}")

        return introspection.data
