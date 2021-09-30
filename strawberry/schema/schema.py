import logging
import sys
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

from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.extensions import Extension
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types import ExecutionContext, ExecutionResult
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion

from ..printer import print_schema
from .config import StrawberryConfig
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
        extensions: Sequence[Union[Type[Extension], Extension]] = (),
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
        config: Optional[StrawberryConfig] = None,
        scalar_overrides: Optional[
            Dict[object, Union[ScalarWrapper, ScalarDefinition]]
        ] = None,
    ):
        self.extensions = extensions
        self.execution_context_class = execution_context_class
        self.config = config or StrawberryConfig()

        scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]] = {
            **DEFAULT_SCALAR_REGISTRY
        }
        if scalar_overrides:
            scalar_registry.update(scalar_overrides)

        self.schema_converter = GraphQLCoreConverter(self.config, scalar_registry)
        self.directives = directives

        query_type = self.schema_converter.from_object(query._type_definition)
        mutation_type = (
            self.schema_converter.from_object(mutation._type_definition)
            if mutation
            else None
        )
        subscription_type = (
            self.schema_converter.from_object(subscription._type_definition)
            if subscription
            else None
        )

        directives = [
            self.schema_converter.from_directive(directive.directive_definition)
            for directive in directives
        ]

        graphql_types = []
        for type_ in types:
            graphql_type = self.schema_converter.from_object(type_._type_definition)
            graphql_types.append(graphql_type)

        self._schema = GraphQLSchema(
            query=query_type,
            mutation=mutation_type,
            subscription=subscription_type if subscription else None,
            directives=specified_directives + directives,
            types=graphql_types,
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

    def process_errors(
        self, errors: List[GraphQLError], execution_context: ExecutionContext
    ) -> None:
        kwargs: Dict[str, Any] = {
            "stack_info": True,
        }

        # stacklevel was added in version 3.8
        # https://docs.python.org/3/library/logging.html#logging.Logger.debug

        if sys.version_info >= (3, 8):
            kwargs["stacklevel"] = 3

        for error in errors:
            logger.error(error, exc_info=error.original_error, **kwargs)

    async def execute(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> ExecutionResult:
        # Create execution context
        execution_context = ExecutionContext(
            query=query,
            schema=self,
            context=context_value,
            root_value=root_value,
            variables=variable_values,
            operation_name=operation_name,
        )

        result = await execute(
            self._schema,
            query,
            extensions=self.extensions,
            directives=self.directives,
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
        )

        if result.errors:
            self.process_errors(result.errors, execution_context=execution_context)

        return result

    def execute_sync(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> ExecutionResult:
        execution_context = ExecutionContext(
            query=query,
            schema=self,
            context=context_value,
            root_value=root_value,
            variables=variable_values,
            operation_name=operation_name,
        )

        result = execute_sync(
            self._schema,
            query,
            extensions=self.extensions,
            directives=self.directives,
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
        )

        if result.errors:
            self.process_errors(result.errors, execution_context=execution_context)

        return result

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
